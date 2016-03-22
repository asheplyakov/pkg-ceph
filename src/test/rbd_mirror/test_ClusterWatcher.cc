// -*- mode:C; tab-width:8; c-basic-offset:2; indent-tabs-mode:t -*-
// vim: ts=8 sw=2 smarttab
#include "include/rados/librados.hpp"
#include "common/Cond.h"
#include "common/errno.h"
#include "common/Mutex.h"
#include "librbd/internal.h"
#include "tools/rbd_mirror/ClusterWatcher.h"
#include "tools/rbd_mirror/types.h"
#include "test/librados/test.h"
#include "gtest/gtest.h"
#include <boost/scope_exit.hpp>
#include <iostream>
#include <map>
#include <memory>
#include <set>

using rbd::mirror::ClusterWatcher;
using rbd::mirror::peer_t;
using rbd::mirror::RadosRef;
using std::map;
using std::set;
using std::string;

void register_test_cluster_watcher() {
}

class TestClusterWatcher : public ::testing::Test {
public:

  TestClusterWatcher() : m_lock("TestClusterWatcherLock")
  {
    m_cluster = std::make_shared<librados::Rados>();
    EXPECT_EQ("", connect_cluster_pp(*m_cluster));
    m_cluster_watcher.reset(new ClusterWatcher(m_cluster, m_lock));
  }

  ~TestClusterWatcher() {
    m_cluster->wait_for_latest_osdmap();
    for (auto& pool : m_pools) {
      EXPECT_EQ(0, m_cluster->pool_delete(pool.c_str()));
    }
  }

  void create_pool(bool enable_mirroring, const peer_t &peer, string *name=nullptr) {
    string pool_name = get_temp_pool_name();
    ASSERT_EQ("", create_one_pool_pp(pool_name, *m_cluster));
    int64_t pool_id = m_cluster->pool_lookup(pool_name.c_str());
    ASSERT_GE(pool_id, 0);
    m_pools.insert(pool_name);
    if (enable_mirroring) {
      librados::IoCtx ioctx;
      ASSERT_EQ(0, m_cluster->ioctx_create2(pool_id, ioctx));
      ASSERT_EQ(0, librbd::mirror_set_enabled(ioctx, true));
      ASSERT_EQ(0, librbd::mirror_peer_add(ioctx, peer.cluster_uuid,
					   peer.cluster_name,
					   peer.client_name));
      m_peer_configs[peer].insert(pool_id);
      m_mirrored_pools.insert(pool_name);
    }
    if (name != nullptr) {
      *name = pool_name;
    }
  }

  void delete_pool(const string &name, const peer_t &peer) {
    int64_t pool_id = m_cluster->pool_lookup(name.c_str());
    ASSERT_GE(pool_id, 0);
    if (m_peer_configs.find(peer) != m_peer_configs.end()) {
      m_peer_configs[peer].erase(pool_id);
      m_mirrored_pools.erase(name);
      if (m_peer_configs[peer].empty()) {
	m_peer_configs.erase(peer);
      }
    }
    m_pools.erase(name);
    ASSERT_EQ(0, m_cluster->pool_delete(name.c_str()));
  }

  void create_cache_pool(const string &base_pool, string *cache_pool_name) {
    bufferlist inbl;
    *cache_pool_name = get_temp_pool_name();
    ASSERT_EQ("", create_one_pool_pp(*cache_pool_name, *m_cluster));
    ASSERT_EQ(0, m_cluster->mon_command(
      "{\"prefix\": \"osd tier add\", \"pool\": \"" + base_pool +
      "\", \"tierpool\": \"" + *cache_pool_name +
      "\", \"force_nonempty\": \"--force-nonempty\" }",
      inbl, NULL, NULL));
    ASSERT_EQ(0, m_cluster->mon_command(
      "{\"prefix\": \"osd tier set-overlay\", \"pool\": \"" + base_pool +
      "\", \"overlaypool\": \"" + *cache_pool_name + "\"}",
      inbl, NULL, NULL));
    ASSERT_EQ(0, m_cluster->mon_command(
      "{\"prefix\": \"osd tier cache-mode\", \"pool\": \"" + *cache_pool_name +
      "\", \"mode\": \"writeback\"}",
      inbl, NULL, NULL));
    m_cluster->wait_for_latest_osdmap();
  }

  void remove_cache_pool(const string &base_pool, const string &cache_pool) {
    bufferlist inbl;
    // tear down tiers
    ASSERT_EQ(0, m_cluster->mon_command(
      "{\"prefix\": \"osd tier remove-overlay\", \"pool\": \"" + base_pool +
      "\"}",
      inbl, NULL, NULL));
    ASSERT_EQ(0, m_cluster->mon_command(
      "{\"prefix\": \"osd tier remove\", \"pool\": \"" + base_pool +
      "\", \"tierpool\": \"" + cache_pool + "\"}",
      inbl, NULL, NULL));
    m_cluster->wait_for_latest_osdmap();
    m_cluster->pool_delete(cache_pool.c_str());
  }

  void check_peers() {
    m_cluster_watcher->refresh_pools();
    Mutex::Locker l(m_lock);
    ASSERT_EQ(m_peer_configs, m_cluster_watcher->get_peer_configs());
    ASSERT_EQ(m_mirrored_pools, m_cluster_watcher->get_pool_names());
  }

  Mutex m_lock;
  RadosRef m_cluster;
  unique_ptr<ClusterWatcher> m_cluster_watcher;

  set<string> m_pools;
  set<string> m_mirrored_pools;
  map<peer_t, set<int64_t> > m_peer_configs;
};

TEST_F(TestClusterWatcher, NoPools) {
  check_peers();
}

TEST_F(TestClusterWatcher, NoMirroredPools) {
  check_peers();
  create_pool(false, peer_t());
  check_peers();
  create_pool(false, peer_t());
  check_peers();
  create_pool(false, peer_t());
  check_peers();
}

TEST_F(TestClusterWatcher, ReplicatedPools) {
  string uuid1 = "00000000-0000-0000-0000-000000000001";
  string uuid2 = "20000000-2222-2222-2222-000000000002";
  peer_t site1(uuid1, "site1", "mirror1");
  peer_t site2(uuid2, "site2", "mirror2");
  string first_pool, last_pool;
  check_peers();
  create_pool(true, site1, &first_pool);
  check_peers();
  create_pool(false, peer_t());
  check_peers();
  create_pool(false, peer_t());
  check_peers();
  create_pool(false, peer_t());
  check_peers();
  create_pool(true, site2);
  check_peers();
  create_pool(true, site2);
  check_peers();
  create_pool(true, site2, &last_pool);
  check_peers();
  delete_pool(first_pool, site1);
  check_peers();
  delete_pool(last_pool, site2);
  check_peers();
}

TEST_F(TestClusterWatcher, CachePools) {
  peer_t site1("11111111-1111-1111-1111-111111111111", "site1", "mirror1");
  string base1, base2, cache1, cache2;
  create_pool(true, site1, &base1);
  check_peers();

  create_cache_pool(base1, &cache1);
  BOOST_SCOPE_EXIT( base1, cache1, this_ ) {
    this_->remove_cache_pool(base1, cache1);
  } BOOST_SCOPE_EXIT_END;
  check_peers();

  create_pool(false, peer_t(), &base2);
  create_cache_pool(base2, &cache2);
  BOOST_SCOPE_EXIT( base2, cache2, this_ ) {
    this_->remove_cache_pool(base2, cache2);
  } BOOST_SCOPE_EXIT_END;
  check_peers();
}
