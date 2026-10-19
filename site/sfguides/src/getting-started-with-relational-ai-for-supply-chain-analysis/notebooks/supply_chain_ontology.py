"""Supply-chain ontology for the RelationalAI supply chain analysis quickstart.

The ontology is the semantic model RelationalAI reasons over: the business concepts
(parts, suppliers, orders, ...), how they relate, and how each Snowflake table maps
onto them. Every later chapter (BOM explosion, supplier failure, buildability, graph
analysis, allocation) queries and extends this one model instead of re-stating joins.

Import it from the notebook:

    from supply_chain_ontology import model, Part, Product, Supplier, Supply, QualifiedSupply, Customer, Order

Model() reads the connection from raiconfig.yaml in the current folder or a parent folder.

Note: this file was generated with generative AI (Cortex Code), not written by hand. It was
validated by loading all tables and checking counts against the source tables. Review the
concepts, keys and mappings before reusing it for your own data.
"""
from relationalai.semantics import Date, Float, Integer, Model, String

SCHEMA = "RAI_QUICKSTART.SUPPLY_CHAIN"

model = Model("SupplyChain")

# =============================================================================
# 1. Concepts: the things the business talks about, each with a stable identity
# =============================================================================
Part = model.Concept("Part", identify_by={"id": String})
Product = model.Concept("Product", identify_by={"id": String})
Supplier = model.Concept("Supplier", identify_by={"id": String})
Customer = model.Concept("Customer", identify_by={"id": String})
Order = model.Concept("Order", identify_by={"id": String})
# A supplier-part pair carries its own data (capacity, lead time, price), so it is a
# concept in its own right rather than a plain link.
Supply = model.Concept("Supply", identify_by={"supplier": Supplier, "part": Part})
# A supplier approved for a part but not supplying it yet: an option, not part of today's network.
QualifiedSupply = model.Concept("QualifiedSupply", identify_by={"supplier": Supplier, "part": Part})

# =============================================================================
# 2. Properties: one value per entity (many-to-one)
# =============================================================================
Part.name = model.Property(f"{Part} is named {String:name}")
Part.kind = model.Property(f"{Part} is of kind {String:kind}")              # FINISHED | ASSEMBLY | COMPONENT
Part.unit_cost = model.Property(f"{Part} costs {Float:unit_cost}")
Part.on_hand = model.Property(f"{Part} has {Integer:on_hand} in stock")

Product.name = model.Property(f"{Product} is named {String:name}")
Product.list_price = model.Property(f"{Product} sells for {Float:list_price}")
Product.top_part = model.Property(f"{Product} is built as {Part:top_part}")

Supplier.name = model.Property(f"{Supplier} is named {String:name}")
Supplier.tier = model.Property(f"{Supplier} is in tier {Integer:tier}")
Supplier.country = model.Property(f"{Supplier} is located in {String:country}")
Supplier.region = model.Property(f"{Supplier} is in region {String:region}")

Supply.capacity_per_week = model.Property(f"{Supply} can deliver {Integer:capacity_per_week} per week")
Supply.lead_time_days = model.Property(f"{Supply} has a lead time of {Integer:lead_time_days} days")
Supply.unit_price = model.Property(f"{Supply} is priced at {Float:unit_price}")

QualifiedSupply.capacity_per_week = model.Property(f"{QualifiedSupply} could deliver {Integer:capacity_per_week} per week")
QualifiedSupply.lead_time_days = model.Property(f"{QualifiedSupply} needs {Integer:lead_time_days} days to start")
QualifiedSupply.unit_price = model.Property(f"{QualifiedSupply} would be priced at {Float:unit_price}")

Customer.name = model.Property(f"{Customer} is named {String:name}")
Customer.region = model.Property(f"{Customer} is in region {String:region}")

Order.customer = model.Property(f"{Order} is placed by {Customer:customer}")
Order.product = model.Property(f"{Order} is for {Product:product}")
Order.quantity = model.Property(f"{Order} asks for {Integer:quantity} units")
Order.due_date = model.Property(f"{Order} is due on {Date:due_date}")
Order.value = model.Property(f"{Order} is worth {Float:value}")

# =============================================================================
# 3. Relationships: links between entities (many-to-many, possibly with data)
#    Same-type slots get role names (parent/child, original/substitute, ...).
# =============================================================================
# Bill of materials: (parent, child) -> quantity. Variable depth, shared subassemblies.
Part.contains = model.Property(f"{Part:parent} contains {Part:child} {Integer:qty} times")
# Approved alternatives: (original, substitute) -> ratio
Part.substitute = model.Property(f"{Part:original} can be replaced by {Part:substitute} at ratio {Float:ratio}")
# Tier-N supply network; may contain cycles
Supplier.depends_on = model.Relationship(f"{Supplier:buyer} depends on {Supplier:upstream}")

# =============================================================================
# 4. Mapping: which table populates which concept, property and relationship
# =============================================================================
parts = model.Table(f"{SCHEMA}.PARTS")
products = model.Table(f"{SCHEMA}.PRODUCTS")
bom = model.Table(f"{SCHEMA}.BOM")
substitutes = model.Table(f"{SCHEMA}.SUBSTITUTES")
inventory = model.Table(f"{SCHEMA}.INVENTORY")
suppliers = model.Table(f"{SCHEMA}.SUPPLIERS")
supplier_parts = model.Table(f"{SCHEMA}.SUPPLIER_PARTS")
supplier_deps = model.Table(f"{SCHEMA}.SUPPLIER_DEPENDENCIES")
customers = model.Table(f"{SCHEMA}.CUSTOMERS")
orders = model.Table(f"{SCHEMA}.ORDERS")
qualified = model.Table(f"{SCHEMA}.QUALIFIED_SUPPLIERS")

model.define(p := Part.new(id=parts.PART_ID),
             p.name(parts.PART_NAME), p.kind(parts.PART_TYPE), p.unit_cost(parts.UNIT_COST))
model.define(Part.lookup(id=inventory.PART_ID).on_hand(inventory.ON_HAND_QTY))

model.define(pr := Product.new(id=products.PRODUCT_ID),
             pr.name(products.PRODUCT_NAME), pr.list_price(products.LIST_PRICE),
             pr.top_part(Part.lookup(id=products.PART_ID)))

model.define(Part.lookup(id=bom.PARENT_PART_ID).contains(Part.lookup(id=bom.CHILD_PART_ID), bom.QTY_PER))
model.define(Part.lookup(id=substitutes.PART_ID).substitute(
    Part.lookup(id=substitutes.SUBSTITUTE_PART_ID), substitutes.RATIO))

model.define(s := Supplier.new(id=suppliers.SUPPLIER_ID),
             s.name(suppliers.SUPPLIER_NAME), s.tier(suppliers.TIER),
             s.country(suppliers.COUNTRY), s.region(suppliers.REGION))
model.define(Supplier.lookup(id=supplier_deps.SUPPLIER_ID).depends_on(
    Supplier.lookup(id=supplier_deps.DEPENDS_ON_SUPPLIER_ID)))

model.define(sp := Supply.new(supplier=Supplier.lookup(id=supplier_parts.SUPPLIER_ID),
                              part=Part.lookup(id=supplier_parts.PART_ID)),
             sp.capacity_per_week(supplier_parts.CAPACITY_PER_WEEK),
             sp.lead_time_days(supplier_parts.LEAD_TIME_DAYS),
             sp.unit_price(supplier_parts.UNIT_PRICE))
model.define(qs := QualifiedSupply.new(supplier=Supplier.lookup(id=qualified.SUPPLIER_ID),
                                       part=Part.lookup(id=qualified.PART_ID)),
             qs.capacity_per_week(qualified.CAPACITY_PER_WEEK),
             qs.lead_time_days(qualified.LEAD_TIME_DAYS),
             qs.unit_price(qualified.UNIT_PRICE))

model.define(c := Customer.new(id=customers.CUSTOMER_ID),
             c.name(customers.CUSTOMER_NAME), c.region(customers.REGION))
model.define(o := Order.new(id=orders.ORDER_ID),
             o.customer(Customer.lookup(id=orders.CUSTOMER_ID)),
             o.product(Product.lookup(id=orders.PRODUCT_ID)),
             o.quantity(orders.QUANTITY), o.due_date(orders.DUE_DATE), o.value(orders.ORDER_VALUE))
