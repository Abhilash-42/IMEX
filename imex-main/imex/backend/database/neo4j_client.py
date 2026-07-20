from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class Neo4jClient:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None
        
    def connect(self):
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            logger.info("Connected to Neo4j")
            return self.driver
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def create_schema(self):
        """Create Neo4j schema with constraints and indexes"""
        with self.driver.session() as session:
            # Create constraints
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Port) REQUIRE p.id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Supplier) REQUIRE s.id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Component) REQUIRE c.id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE")
            
            # Create indexes
            session.run("CREATE INDEX IF NOT EXISTS FOR (p:Port) ON (p.name)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (s:Supplier) ON (s.name)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (c:Component) ON (c.name)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (p:Product) ON (p.name)")
            
            logger.info("Neo4j schema created")
    
    def create_port(self, port_data):
        """Create a port node"""
        with self.driver.session() as session:
            result = session.run("""
                CREATE (p:Port {
                    id: $id,
                    name: $name,
                    country: $country,
                    city: $city,
                    latitude: $latitude,
                    longitude: $longitude,
                    is_active: $is_active
                })
                RETURN p
            """, **port_data)
            return result.single()
    
    def create_supplier(self, supplier_data):
        """Create a supplier node"""
        with self.driver.session() as session:
            result = session.run("""
                CREATE (s:Supplier {
                    id: $id,
                    name: $name,
                    country: $country,
                    city: $city,
                    criticality_score: $criticality_score,
                    reliability_score: $reliability_score,
                    is_active: $is_active
                })
                RETURN s
            """, **supplier_data)
            return result.single()
    
    def create_component(self, component_data):
        """Create a component node"""
        with self.driver.session() as session:
            result = session.run("""
                CREATE (c:Component {
                    id: $id,
                    name: $name,
                    description: $description,
                    criticality: $criticality,
                    lead_time_days: $lead_time_days,
                    cost_per_unit: $cost_per_unit
                })
                RETURN c
            """, **component_data)
            return result.single()
    
    def create_product(self, product_data):
        """Create a product node"""
        with self.driver.session() as session:
            result = session.run("""
                CREATE (p:Product {
                    id: $id,
                    name: $name,
                    description: $description,
                    revenue_per_unit: $revenue_per_unit,
                    monthly_sales: $monthly_sales,
                    business_unit: $business_unit
                })
                RETURN p
            """, **product_data)
            return result.single()
    
    def create_relationship(self, source_id, target_id, relationship_type, properties=None):
        """Create a relationship between two nodes"""
        with self.driver.session() as session:
            query = f"""
                MATCH (source {{id: $source_id}})
                MATCH (target {{id: $target_id}})
                CREATE (source)-[r:{relationship_type}]->(target)
                SET r += $properties
                RETURN r
            """
            result = session.run(
                query,
                source_id=source_id,
                target_id=target_id,
                properties=properties or {}
            )
            return result.single()
    
    def get_supply_chain_path(self, product_id):
        """Get the complete supply chain path for a product"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH path = (p:Product {id: $product_id})
                <-[:USED_IN]-(c:Component)
                <-[:PROVIDES]-(s:Supplier)
                <-[:SUPPLIES]-(port:Port)
                RETURN path, nodes(path) as nodes, relationships(path) as relationships
            """, product_id=product_id)
            return [{"nodes": record["nodes"], "relationships": record["relationships"]} 
                    for record in result]
    
    def get_affected_suppliers(self, port_id):
        """Get all suppliers affected by a port disruption"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (port:Port {id: $port_id})
                -[:SUPPLIES]->(s:Supplier)
                RETURN s.id as id, s.name as name, s.criticality_score as criticality_score
                ORDER BY s.criticality_score DESC
            """, port_id=port_id)
            return [record.data() for record in result]
    
    def get_affected_products(self, supplier_id):
        """Get all products affected by a supplier disruption"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:Supplier {id: $supplier_id})
                -[:PROVIDES]->(c:Component)
                -[:USED_IN]->(p:Product)
                RETURN p.id as id, p.name as name, p.revenue_per_unit as revenue_per_unit,
                       p.monthly_sales as monthly_sales
                ORDER BY p.revenue_per_unit * p.monthly_sales DESC
            """, supplier_id=supplier_id)
            return [record.data() for record in result]
    
    def get_impact_path(self, event_location):
        """Get the full impact path from location to products"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (port:Port {country: $event_location})
                -[:SUPPLIES]->(s:Supplier)
                -[:PROVIDES]->(c:Component)
                -[:USED_IN]->(p:Product)
                RETURN port.name as port_name, 
                       collect(DISTINCT s.name) as suppliers,
                       collect(DISTINCT c.name) as components,
                       collect(DISTINCT p.name) as products
            """, event_location=event_location)
            return result.single()

# Singleton instance
neo4j_client = Neo4jClient()