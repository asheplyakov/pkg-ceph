// -*- mode:C++; tab-width:4; c-basic-offset:2; indent-tabs-mode:t -*- 
/*
 * Ceph - scalable distributed file system
 *
 * Copyright (C) 2004-2006 Sage Weil <sage@newdream.net>
 *
 * This is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License version 2.1, as published by the Free Software 
 * Foundation.  See file COPYING.
 * 
 */



#include <ext/hash_map>
using namespace __gnu_cxx;

#include "include/Context.h"
#include "include/bufferlist.h"

#include "types.h"
#include "Onode.h"
#include "Cnode.h"
#include "BlockDevice.h"
#include "nodes.h"
#include "Allocator.h"
#include "Table.h"
#include "AlignedBufferPool.h"

#include "common/Mutex.h"
#include "common/Cond.h"

#include "osd/ObjectStore.h"

typedef pair<object_t,coll_t> idpair_t;

inline ostream& operator<<(ostream& out, idpair_t oc) {
  return out << hex << oc.first << "->" << oc.second << dec;
}



class Ebofs : public ObjectStore {
 protected:
  Mutex        ebofs_lock;    // a beautiful global lock

  // ** super **
  BlockDevice  dev;
  bool         mounted, unmounting, dirty;
  bool         readonly;
  version_t    super_epoch;
  bool         commit_thread_started, mid_commit;
  Cond         commit_cond;   // to wake up the commit thread
  Cond         sync_cond;

  map<version_t, list<Context*> > commit_waiters;

  void prepare_super(version_t epoch, bufferptr& bp);
  void write_super(version_t epoch, bufferptr& bp);
  int commit_thread_entry();

  class CommitThread : public Thread {
	Ebofs *ebofs;
  public:
	CommitThread(Ebofs *e) : ebofs(e) {}
	void *entry() {
	  ebofs->commit_thread_entry();
	  return 0;
	}
  } commit_thread;

  


  // ** allocator **
  block_t      free_blocks, limbo_blocks;
  Allocator    allocator;
  friend class Allocator;
  
  block_t get_free_blocks() { return free_blocks; }
  block_t get_limbo_blocks() { return limbo_blocks; }
  block_t get_free_extents() { 
	int n = 0;
	for (int i=0; i<EBOFS_NUM_FREE_BUCKETS; i++) 
	  n += free_tab[i]->get_num_keys();
	return n;
  }
  block_t get_limbo_extents() { return limbo_tab->get_num_keys(); }


  // ** buffers **
  AlignedBufferPool bufferpool;
  

  // ** tables and sets **
  // nodes
  NodePool     nodepool;   // for all tables...

  // tables
  Table<object_t, Extent> *object_tab;
  Table<block_t,block_t>  *free_tab[EBOFS_NUM_FREE_BUCKETS];
  Table<block_t,block_t>  *limbo_tab;

  // collections
  Table<coll_t, Extent>  *collection_tab;
  Table<idpair_t, bool>  *oc_tab;
  Table<idpair_t, bool>  *co_tab;

  void close_tables();


  // ** onodes **
  hash_map<object_t, Onode*>  onode_map;  // onode cache
  LRU                         onode_lru;
  set<Onode*>                 dirty_onodes;
  map<object_t, list<Cond*> > waitfor_onode;

  Onode* new_onode(object_t oid);     // make new onode.  ref++.
  Onode* get_onode(object_t oid);     // get cached onode, or read from disk.  ref++.
  void remove_onode(Onode *on);
  void put_onode(Onode* o);         // put it back down.  ref--.
  void dirty_onode(Onode* o);
  void encode_onode(Onode *on, bufferlist& bl, unsigned& off);
  void write_onode(Onode *on);

  // ** cnodes **
  hash_map<coll_t, Cnode*>    cnode_map;
  LRU                         cnode_lru;
  set<Cnode*>                 dirty_cnodes;
  map<object_t, list<Cond*> > waitfor_cnode;

  Cnode* new_cnode(coll_t cid);
  Cnode* get_cnode(coll_t cid);
  void remove_cnode(Cnode *cn);
  void put_cnode(Cnode *cn);
  void dirty_cnode(Cnode *cn);
  void encode_cnode(Cnode *cn, bufferlist& bl, unsigned& off);
  void write_cnode(Cnode *cn);

  // ** onodes+cnodes = inodes **
  int                         inodes_flushing;
  Cond                        inode_commit_cond;                    

  void flush_inode_finish();
  void commit_inodes_start();
  void commit_inodes_wait();
  friend class C_E_InodeFlush;

  void trim_inodes(int max = -1);

  // ** buffer cache **
  BufferCache bc;
  pthread_t flushd_thread_id;

  version_t trigger_commit();
  void commit_bc_wait(version_t epoch);
  void trim_bc(off_t max = -1);

 public:
  void kick_idle();
  void sync();
  void trim_buffer_cache();

  class IdleKicker : public BlockDevice::kicker {
	Ebofs *ebo;
  public:
	IdleKicker(Ebofs *t) : ebo(t) {}
	void kick() { ebo->kick_idle(); }
  } idle_kicker;


 protected:
  //void zero(Onode *on, size_t len, off_t off, off_t write_thru);
  void alloc_write(Onode *on, 
				   block_t start, block_t len, 
				   interval_set<block_t>& alloc,
				   block_t& old_bfirst, block_t& old_blast);
  void apply_write(Onode *on, size_t len, off_t off, bufferlist& bl);
  bool attempt_read(Onode *on, size_t len, off_t off, bufferlist& bl, 
					Cond *will_wait_on, bool *will_wait_on_bool);

  // ** finisher **
  // async write notification to users
  Mutex          finisher_lock;
  Cond           finisher_cond;
  bool           finisher_stop;
  list<Context*> finisher_queue;

  int finisher_thread_entry();
  class FinisherThread : public Thread {
	Ebofs *ebofs;
  public:
	FinisherThread(Ebofs *e) : ebofs(e) {}
	void* entry() { return (void*)ebofs->finisher_thread_entry(); }
  } finisher_thread;


  bool _write_will_block();
  void alloc_more_node_space();

  void do_csetattrs(map<coll_t, map<const char*, pair<void*,int> > > &cmods);
  void do_setattrs(Onode *on, map<const char*, pair<void*,int> > &setattrs);


 public:
  Ebofs(char *devfn) : 
	dev(devfn), 
	mounted(false), unmounting(false), dirty(false), readonly(false), 
	super_epoch(0), commit_thread_started(false), mid_commit(false),
	commit_thread(this),
	free_blocks(0), limbo_blocks(0),
	allocator(this),
	bufferpool(EBOFS_BLOCK_SIZE),
	nodepool(ebofs_lock),
	object_tab(0), limbo_tab(0), collection_tab(0), oc_tab(0), co_tab(0),
	onode_lru(g_conf.ebofs_oc_size),
	cnode_lru(g_conf.ebofs_cc_size),
	inodes_flushing(0),
	bc(dev, bufferpool, ebofs_lock),
	idle_kicker(this),
	finisher_stop(false), finisher_thread(this) {
	for (int i=0; i<EBOFS_NUM_FREE_BUCKETS; i++)
	  free_tab[i] = 0;
  }
  ~Ebofs() {
  }

  int mkfs();
  int mount();
  int umount();
  
  int statfs(struct statfs *buf);


  // object interface
  bool exists(object_t);
  int stat(object_t, struct stat*);
  int read(object_t, size_t len, off_t off, bufferlist& bl);
  int write(object_t oid, 
			size_t len, off_t off, 
			bufferlist& bl, bool fsync=true);
  int write(object_t oid, 
			size_t len, off_t offset, 
			bufferlist& bl, 
			Context *onsafe);
  int write_transaction(object_t oid, 
						size_t len, off_t offset, 
						bufferlist& bl, 
						map<const char*, pair<void*,int> >& setattrs,
						map<coll_t, map<const char*, pair<void*,int> > >& cmods,
						Context *onsafe);

  int truncate(object_t oid, off_t size,
			   Context *onsafe=0);
  int truncate_transaction(object_t oid, off_t size, 
						   map<const char*, pair<void*,int> >& setattrs,
						   map<coll_t, map<const char*, pair<void*,int> > >& cmods,
						   Context *onsafe);

  int remove(object_t oid,
			 Context *onsafe=0);
  int remove_transaction(object_t,
						 map<coll_t, map<const char*, pair<void*,int> > >& cmods,
						 Context *onsafe=0);

  bool write_will_block();

  // object attr
  int setattr(object_t oid, const char *name, const void *value, size_t size,
			  Context *onsafe=0);
  int getattr(object_t oid, const char *name, void *value, size_t size);
  int rmattr(object_t oid, const char *name,
			 Context *onsafe=0);
  int listattr(object_t oid, vector<string>& attrs);
  
  // collections
  int list_collections(list<coll_t>& ls);
  //int collection_stat(coll_t c, struct stat *st);
  int create_collection(coll_t c);
  int destroy_collection(coll_t c);

  bool _collection_exists(coll_t c);
  bool collection_exists(coll_t c);
  int collection_add(coll_t c, object_t o);
  int collection_remove(coll_t c, object_t o);
  int collection_list(coll_t c, list<object_t>& o);
  
  int collection_setattr(object_t oid, const char *name, const void *value, size_t size);
  int collection_getattr(object_t oid, const char *name, void *value, size_t size);
  int collection_rmattr(coll_t cid, const char *name);
  int collection_listattr(object_t oid, vector<string>& attrs);
  
};
