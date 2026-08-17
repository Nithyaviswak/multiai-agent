from app.agents.planner_agent import classify_action


def test_classify_configure():
    assert classify_action("Configure OSPF on core-router-01") == "configure"
    assert classify_action("deploy the new vlan config") == "configure"
    assert classify_action("start bgp on edge-router") == "configure"


def test_classify_verify():
    assert classify_action("Verify OSPF neighbors on core-router-01") == "verify"
    assert classify_action("check connectivity between routers") == "verify"
    assert classify_action("validate the config was applied") == "verify"


def test_classify_troubleshoot():
    assert classify_action("Troubleshoot why link is down") == "troubleshoot"
    assert classify_action("the interface is not working") == "troubleshoot"


def test_classify_backup_and_audit():
    assert classify_action("Backup the running config") == "backup"
    assert classify_action("audit security compliance") == "audit"


def test_classify_default_is_analyze():
    assert classify_action("What do you think about the network") == "analyze"


def test_technology_extraction():
    from app.agents.planner_agent import PlannerAgent
    agent = PlannerAgent()
    assert agent._extract_technology("configure bgp peering") == "BGP"
    assert agent._extract_technology("set up a new vlan") == "VLAN"
    assert agent._extract_technology("deploy access control lists") == "ACL"
    assert agent._extract_technology("check ospf adjacency") == "OSPF"


def test_device_extraction():
    from app.agents.planner_agent import PlannerAgent
    agent = PlannerAgent()
    assert agent._extract_devices("configure ospf on core-router-01 and edge-router-01") == \
        ["core-router-01", "edge-router-01"]
    # Non-inventory strings should not be treated as devices.
    assert agent._extract_devices("no devices mentioned here") == []