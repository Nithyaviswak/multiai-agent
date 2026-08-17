from typing import Dict, Any, List, Optional
from app.agents.base import BaseAgent
from app.tools.calling.search_tool import search_tool
from app.logging_config import logger

class KnowledgeAgent(BaseAgent):
    """Knowledge Agent with hybrid search (web + simulated internal docs)"""

    INTERNAL_KB = {
        "ospf configuration": "OSPF configuration on Cisco IOS-XE: router ospf <process-id>, network <network> <wildcard> area <area>",
        "vlan configuration": "VLAN configuration: vlan <id>, name <name>, interface <type> switchport mode access/trunk, switchport access vlan <id>",
        "bgp configuration": "BGP configuration: router bgp <asn>, neighbor <ip> remote-as <asn>, address-family ipv4, neighbor <ip> activate",
        "acl configuration": "ACL: ip access-list extended <name>, permit/deny <protocol> <src> <dst>, interface <name> ip access-group <name> in/out",
        "ntp configuration": "NTP: ntp server <ip-address>, ntp source <interface>",
        "snmp configuration": "SNMP: snmp-server community <string> ro/rw, snmp-server trap-source <interface>",
        "password encryption": "service password-encryption, enable secret <password>, username <name> secret <password>",
        "ssh configuration": "ip domain-name <domain>, crypto key generate rsa modulus 2048, ip ssh version 2, line vty 0 4 transport input ssh",
        "cisco ios commands": "Common show commands: show version, show running-config, show ip interface brief, show interfaces, show vlan brief, show ip route, show cdp neighbors",
    }

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("intent", "")
        logger.info("Knowledge agent started")

        try:
            internal_results = self._search_internal(query)
            web_results = await search_tool.execute(query, max_results=3)
            combined = {
                "internal_knowledge": internal_results,
                "web_sources": web_results.get("results", []),
                "total_sources": len(internal_results) + len(web_results.get("results", [])),
            }
            return {
                "knowledge_data": combined,
                "knowledge_complete": True,
                "current_step": "knowledge",
            }
        except Exception as e:
            logger.error("Knowledge agent failed", error=str(e))
            return {
                "knowledge_data": {"error": str(e)},
                "knowledge_complete": False,
                "errors": state.get("errors", []) + [f"Knowledge retrieval failed: {str(e)}"],
            }

    def _search_internal(self, query: str) -> List[Dict[str, str]]:
        query_lower = query.lower()
        results = []
        for keyword, doc in self.INTERNAL_KB.items():
            if any(word in query_lower for word in keyword.split()):
                results.append({"source": "internal_kb", "keyword": keyword, "content": doc})
        return results
