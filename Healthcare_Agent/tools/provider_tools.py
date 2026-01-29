"""
Provider and Location Selection Tools
Help patients find providers and clinic locations
"""
from typing import Dict, Any
from tools.base_tool import BaseTool


class SelectProviderTool(BaseTool):
    """Select a healthcare provider"""
    
    def __init__(self, dynamodb, providers_table, audit_logger):
        super().__init__(dynamodb)
        self.providers_table = providers_table
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        List providers by specialty or search criteria
        
        Args:
            specialty: Optional specialty filter
            locationId: Optional location filter
            acceptingNewPatients: Optional filter (default: True)
            sessionId: Session identifier
            
        Returns:
            providers: List of matching providers
            count: Number found
        """
        try:
            specialty = content_data.get("specialty")
            location_id = content_data.get("locationId")
            accepting_new = content_data.get("acceptingNewPatients", True)
            session_id = content_data.get("sessionId")
            
            # Build filter
            filter_parts = []
            expr_values = {}
            
            if accepting_new:
                filter_parts.append("acceptingNewPatients = :anp")
                expr_values[':anp'] = True
            
            if specialty:
                filter_parts.append("specialty = :spec")
                expr_values[':spec'] = specialty
            
            if location_id:
                filter_parts.append("contains(locations, :loc)")
                expr_values[':loc'] = location_id
            
            if filter_parts:
                filter_expr = " AND ".join(filter_parts)
                response = self.providers_table.scan(
                    FilterExpression=filter_expr,
                    ExpressionAttributeValues=expr_values
                )
            else:
                response = self.providers_table.scan()
            
            providers = response.get('Items', [])
            providers = [self.convert_decimals(p) for p in providers]
            
            # Sort by name
            providers.sort(key=lambda x: x.get('name', ''))
            
            # Limit results
            providers = providers[:15]
            
            # Audit log (no PHI accessed)
            self.audit_logger.log_event(
                event_type='PROVIDER',
                user_id=None,
                session_id=session_id,
                action='SEARCH_PROVIDERS',
                success=True,
                phi_accessed=False,
                details={'results_count': len(providers), 'specialty': specialty}
            )
            
            return {
                "success": True,
                "providers": providers,
                "count": len(providers),
                "message": f"Found {len(providers)} provider(s) matching your criteria."
            }
            
        except Exception as e:
            return {"error": str(e)}


class SelectLocationTool(BaseTool):
    """Select a clinic location"""
    
    def __init__(self, dynamodb, locations_table, audit_logger):
        super().__init__(dynamodb)
        self.locations_table = locations_table
        self.audit_logger = audit_logger
    
    def execute(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        List clinic locations
        
        Args:
            servicesOffered: Optional filter by services
            city: Optional city filter
            sessionId: Session identifier
            
        Returns:
            locations: List of clinic locations
            count: Number found
        """
        try:
            services = content_data.get("servicesOffered")
            city = content_data.get("city")
            session_id = content_data.get("sessionId")
            
            # Build filter
            filter_parts = []
            expr_values = {}
            
            if services:
                filter_parts.append("contains(servicesOffered, :svc)")
                expr_values[':svc'] = services
            
            if city:
                filter_parts.append("city = :city")
                expr_values[':city'] = city
            
            if filter_parts:
                filter_expr = " AND ".join(filter_parts)
                response = self.locations_table.scan(
                    FilterExpression=filter_expr,
                    ExpressionAttributeValues=expr_values
                )
            else:
                response = self.locations_table.scan()
            
            locations = response.get('Items', [])
            locations = [self.convert_decimals(loc) for loc in locations]
            
            # Sort by name
            locations.sort(key=lambda x: x.get('name', ''))
            
            # Audit log (no PHI)
            self.audit_logger.log_event(
                event_type='LOCATION',
                user_id=None,
                session_id=session_id,
                action='SEARCH_LOCATIONS',
                success=True,
                phi_accessed=False,
                details={'results_count': len(locations)}
            )
            
            return {
                "success": True,
                "locations": locations,
                "count": len(locations),
                "message": f"Found {len(locations)} location(s)."
            }
            
        except Exception as e:
            return {"error": str(e)}
