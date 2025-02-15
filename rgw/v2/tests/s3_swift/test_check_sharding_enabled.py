""" test_check_sharding_enabled.py

Usage: test_check_sharding_enabled.py -c <input_yaml>

<input_yaml>
	Note: Any one of these yamls can be used
	test_check_sharding_enabled_brownfield.yaml
    test_check_sharding_enabled_greenfield.yaml
	
"""
# test sharding enabled on cluster
import os
import sys

sys.path.append(os.path.abspath(os.path.join(__file__, "../../../..")))
import argparse
import hashlib
import json
import logging
import time
import traceback

import v2.lib.resource_op as s3lib
import v2.utils.utils as utils
from v2.lib.exceptions import RGWBaseException, TestExecError
from v2.lib.resource_op import Config
from v2.lib.rgw_config_opts import CephConfOp, ConfigOpts
from v2.lib.s3.auth import Auth
from v2.lib.s3.write_io_info import BasicIOInfoStructure, IOInfoInitialize
from v2.tests.s3_swift import reusable
from v2.utils.log import configure_logging
from v2.utils.test_desc import AddTestInfo
from v2.utils.utils import RGWService

log = logging.getLogger()
TEST_DATA_PATH = None


def test_exec(config, ssh_con):

    io_info_initialize = IOInfoInitialize()
    basic_io_structure = BasicIOInfoStructure()
    io_info_initialize.initialize(basic_io_structure.initial())
    ceph_conf = CephConfOp(ssh_con)
    rgw_service = RGWService()

    if config.dbr_scenario == "brownfield":
        log.info("Check sharding is enabled or not")
        cmd = "radosgw-admin zonegroup get"
        out = utils.exec_shell_cmd(cmd)
        zonegroup = json.loads(out)
        if zonegroup.get("enabled_features"):
            zonegroup = zonegroup.get("enabled_features")
            log.info(zonegroup)
            if "resharding" in zonegroup:
                log.info("sharding is enabled")
        else:
            log.info("sharding is not enabled")
            if config.enable_sharding is True:
                log.info("Enabling sharding on cluster since cluster is brownfield")
                cmd = "radosgw-admin zonegroup get"
                out = utils.exec_shell_cmd(cmd)
                zonegroup = json.loads(out)
                zonegroup_name = zonegroup.get("name")
                log.info(zonegroup_name)
                cmd = (
                    "radosgw-admin zonegroup modify --rgw-zonegroup=%s --enable-feature=resharding"
                    % zonegroup_name
                )
                out = utils.exec_shell_cmd(cmd)
                cmd = "radosgw-admin period update --commit"
                out = utils.exec_shell_cmd(cmd)
                cmd = "radosgw-admin zonegroup get"
                out = utils.exec_shell_cmd(cmd)
                zonegroup = json.loads(out)
                zonegroup = zonegroup.get("enabled_features")
                log.info(zonegroup)
                if "resharding" in zonegroup:
                    log.info("sharding is enabled")
                else:
                    raise TestExecError("sharding has not enabled")
            else:
                raise TestExecError("sharding has not enabled")

    if config.dbr_scenario == "greenfield":
        log.info("Check sharding is enabled or not")
        cmd = "radosgw-admin zonegroup get"
        out = utils.exec_shell_cmd(cmd)
        zonegroup = json.loads(out)
        zonegroup = zonegroup.get("enabled_features")
        log.info(zonegroup)
        if "resharding" in zonegroup:
            log.info("sharding has enabled already")
        else:
            raise TestExecError("sharding has not enabled already")


if __name__ == "__main__":

    test_info = AddTestInfo("sharding enabled check")
    test_info.started_info()

    try:
        project_dir = os.path.abspath(os.path.join(__file__, "../../.."))
        test_data_dir = "test_data"
        rgw_service = RGWService()
        TEST_DATA_PATH = os.path.join(project_dir, test_data_dir)
        log.info("TEST_DATA_PATH: %s" % TEST_DATA_PATH)
        if not os.path.exists(TEST_DATA_PATH):
            log.info("test data dir not exists, creating.. ")
            os.makedirs(TEST_DATA_PATH)
        parser = argparse.ArgumentParser(description="RGW S3 Automation")
        parser.add_argument("-c", dest="config", help="RGW Test yaml configuration")
        parser.add_argument(
            "-log_level",
            dest="log_level",
            help="Set Log Level [DEBUG, INFO, WARNING, ERROR, CRITICAL]",
            default="info",
        )
        parser.add_argument(
            "--rgw-node", dest="rgw_node", help="RGW Node", default="127.0.0.1"
        )
        args = parser.parse_args()
        yaml_file = args.config
        rgw_node = args.rgw_node
        ssh_con = None
        if rgw_node != "127.0.0.1":
            ssh_con = utils.connect_remote(rgw_node)
        log_f_name = os.path.basename(os.path.splitext(yaml_file)[0])
        configure_logging(f_name=log_f_name, set_level=args.log_level.upper())
        config = Config(yaml_file)
        ceph_conf = CephConfOp(ssh_con)
        config.read(ssh_con)

        test_exec(config, ssh_con)
        test_info.success_status("test passed")
        sys.exit(0)

    except (RGWBaseException, Exception) as e:
        log.error(e)
        log.error(traceback.format_exc())
        test_info.failed_status("test failed")
        sys.exit(1)
