# Instructions
Create a Semantic View for sales analytics on the Facts and Dimensions at HOL_COCO_COWORK.DATA schema. 

## Specifications
- **Role**: Use role ACCOUNTADMIN
- **Semantic View Name**: hot_food_sales_analytics  
- **Target Location**: HOL_COCO_COWORK.TOOLS  
- **Source Tables**: All tables in HOL_COCO_COWORK.DATA (FACT_ITEM_SALES, DIM_ITEM, DIM_STORE)  
- **Include all columns** from every table  
- **Relationships**: Infer from foreign keys (FACT_ITEM_SALES → DIM_ITEM via ITEM_ID, FACT_ITEM_SALES → DIM_STORE via STORE_ID)  

## Verified Queries (VQRs)

Include verified queries for these sales analytics questions:

1. What is the total revenue?
2. What is the total revenue by category?
3. What is the total revenue by state?
4. What are the top 10 stores by revenue?
5. What are the top 10 best selling items by quantity?
6. What is the monthly revenue trend?
7. What is the average discount percentage by category?
8. How many total transactions are there?

## Deploy

After validation passes, deploy the semantic view to HOL_COCO_COWORK.TOOLS.
