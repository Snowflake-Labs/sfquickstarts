/*=============================================================
  05 — Load Unstructured (Free-Text) Data
  370+ rows: SUPPLIER_EMAILS + WAREHOUSE_INSPECTION_NOTES
  NOTE: LOGISTICS_INCIDENT_REPORTS excluded — data lives in Amazon S3
=============================================================*/

USE DATABASE SUPPLY_CHAIN_DEMO;
USE SCHEMA PUBLIC;
USE WAREHOUSE SUPPLY_CHAIN_WH;

-- ============================================================
-- SUPPLIER_EMAILS (200 rows)
-- ============================================================

INSERT INTO SUPPLIER_EMAILS (SUPPLIER_ID, SUPPLIER_NAME, SENDER, SUBJECT, EMAIL_BODY, DATE_SENT, PRIORITY) VALUES
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Technology Upgrade Announcement', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Wei Chen', '2024-12-10', 'Medium'),
(2, 'EuroTech Components', 'anna.mueller@eurotech.de', 'Technology Upgrade Announcement', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Anna Mueller', '2025-01-10', 'Low'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Force Majeure Declaration', 'Dear Valued Customer,

Due to raw material shortage, we must implement a price increase of 24% across affected product lines effective January 20. We understand this is significant and are open to discussing volume-based discounts.

Best regards,
Wei Chen', '2024-12-27', 'Medium'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'New Product Line Launch', 'Dear Team,

This is to confirm that PO-5121 has been delivered on schedule. All 200 units passed outgoing quality inspection with a 0.0% defect rate. Please confirm receipt.

Best regards,
Wei Chen', '2025-01-14', 'Medium'),
(15, 'Santiago Copper Mining', 'exportaciones@santiagocm.cl', 'Volume Discount Offer 2025', 'Dear Partner,

We are pleased to share our Q1 2025 product catalog. As a valued partner, we are offering a 17% early-order discount on orders placed before January 31st. Our production capacity has expanded by 27%.

Warm regards,
Exportaciones', '2025-01-01', 'Low'),
(12, 'Toronto Safety Supplies', 'dispatch@torontosafety.ca', 'Shipment Confirmation - TOR-2024-1127', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 5 days, express option available at 3 days, safety stock maintained at our warehouse.

Best regards,
Dispatch', '2024-12-27', 'Medium'),
(8, 'TechnoPlast Brazil', 'carlos.silva@technoplast.br', 'Seasonal Forecast Q1-Q2 2025', 'Dear QA Team,

The independent lab results for batch TEC-2024-977 are now available. All samples met or exceeded requirements. We are ready to begin volume production upon your confirmation.

Regards,
Carlos Silva', '2024-12-12', 'Medium'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Force Majeure Declaration', 'Hello,

Following your quality inspection report, we acknowledge that batch SHE-2024-814 had a defect rate of 8.3%, which is above the contractual threshold. The issue was traced to incorrect raw material batch. We have implemented corrective actions and will ship replacements by January 20.

Regards,
Wei Chen', '2024-12-28', 'Medium'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Shipping Route Change Advisory', 'Hello,

Following your quality inspection report, we acknowledge that batch MUM-2024-1022 had a defect rate of 3.6%, which is above the contractual threshold. The issue was traced to humidity exposure during storage. We have implemented corrective actions and will ship replacements by January 11.

Regards,
Rajesh Patel', '2024-12-21', 'Medium'),
(8, 'TechnoPlast Brazil', 'carlos.silva@technoplast.br', 'Technology Upgrade Announcement', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 18 days, express option available at 3 days, safety stock maintained at our warehouse.

Best regards,
Carlos Silva', '2024-12-02', 'Medium'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'Force Majeure Declaration', 'Hello,

Following your quality inspection report, we acknowledge that batch CAP-2024-1003 had a defect rate of 3.1%, which is above the contractual threshold. The issue was traced to humidity exposure during storage. We have implemented corrective actions and will ship replacements by February 09.

Regards,
James Botha', '2025-01-11', 'High'),
(3, 'Great Lakes Packaging', 'orders@greatlakespkg.com', 'Inventory Availability Confirmation', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Orders', '2024-12-31', 'Medium'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'RE: Recurring Quality Complaints', 'Hello,

Due to raw material shortage, our shipping partners have rerouted vessels via alternative routes. This adds approximately 20 days to transit times. We are exploring air freight for urgent orders at 14% cost premium.

Regards,
James Botha', '2024-12-05', 'Medium'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Volume Discount Offer 2025', 'Dear Purchasing,

Given current market conditions, we would like to offer a price lock arrangement for the next 15 months at favorable rates. Please respond by January 10 to secure these terms.

Regards,
Wei Chen', '2024-12-17', 'Low'),
(8, 'TechnoPlast Brazil', 'carlos.silva@technoplast.br', 'Quality Certificates - Batch TEC-2024-967', 'Dear Partner,

We are pleased to share our Q1 2025 product catalog. As a valued partner, we are offering a 22% early-order discount on orders placed before January 31st. Our production capacity has expanded by 15%.

Warm regards,
Carlos Silva', '2024-12-08', 'Low'),
(1, 'Pacific Rim Electronics', 'sales@pacificrim.com', 'On-Time Delivery Confirmation - PO-5121', 'Dear Partner,

We are pleased to share our Q1 2025 product catalog. As a valued partner, we are offering a 11% early-order discount on orders placed before January 31st. Our production capacity has expanded by 21%.

Warm regards,
Sales', '2024-12-27', 'Low'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'Sustainability Initiative Update', 'Dear Procurement,

We are excited to announce our new precision bearing product line featuring improved specifications and competitive pricing at only 5% premium over standard products.

Best regards,
Siti Rahman', '2025-01-02', 'Low'),
(12, 'Toronto Safety Supplies', 'dispatch@torontosafety.ca', 'Shipment Confirmation - TOR-2024-810', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Dispatch', '2024-12-19', 'Medium'),
(9, 'Yokohama Precision', 'tanaka.h@yokohamaprecision.jp', 'Lead Time Reduction Update', 'Dear QA Team,

The independent lab results for batch YOK-2024-819 are now available. All samples met or exceeded requirements. We are ready to begin volume production upon your confirmation.

Regards,
Tanaka H', '2024-12-18', 'Medium'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'New Product Line Launch', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 15 days, express option available at 4 days, safety stock maintained at our warehouse.

Best regards,
Wei Chen', '2025-01-12', 'Low'),
(19, 'Milan Olive Oil Co.', 'export@milanoliveoil.it', 'Lead Time Reduction Update', 'Dear Team,

This is to confirm that PO-5152 has been delivered on schedule. All 1000 units passed outgoing quality inspection with a 0.0% defect rate. Please confirm receipt.

Best regards,
Export', '2025-01-15', 'Medium'),
(14, 'Guangzhou Textiles', 'lisa.wong@guangzhoutex.cn', 'Supply Shortage Alert', 'Hello,

Following your quality inspection report, we acknowledge that batch GUA-2024-1139 had a defect rate of 6.8%, which is above the contractual threshold. The issue was traced to a calibration error in assembly. We have implemented corrective actions and will ship replacements by January 19.

Regards,
Lisa Wong', '2024-12-29', 'High'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Quality Issue - Batch SHE-2024-1095', 'Dear Supply Chain Team,

I am writing to inform you of a critical situation at our facility. a major equipment failure. This will impact the following open purchase orders: PO-5138 and PO-5034. We are exploring all options including subcontracting.

Sincerely,
Wei Chen', '2024-12-22', 'High'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'Sustainability Initiative Update', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Siti Rahman', '2024-12-16', 'Low'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'Quality Issue - Batch JAK-2024-1000', 'Dear Team,

We have been notified that shipment JAK-2024-1000 has been held at customs due to supply chain disruption. We expect a 14-day delay. This is being resolved and we apologize for the inconvenience.

Siti Rahman', '2024-12-18', 'Medium');

INSERT INTO SUPPLIER_EMAILS (SUPPLIER_ID, SUPPLIER_NAME, SENDER, SUBJECT, EMAIL_BODY, DATE_SENT, PRIORITY) VALUES
(18, 'Seoul Semiconductor', 'park.jh@seoulsemi.kr', 'Price Increase Notification', 'Dear Team,

We have been notified that shipment SEO-2024-1183 has been held at customs due to regulatory compliance delays. We expect a 15-day delay. This is being resolved and we apologize for the inconvenience.

Park Jh', '2024-12-16', 'High'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'RE: Recurring Quality Complaints', 'Dear Logistics Team,

We are experiencing regulatory compliance delays at our primary warehouse affecting approximately 6% of finished goods. Insurance claims are being filed. We estimate a 12-week delay for affected orders.

Operations Team,
Rajesh Patel', '2025-01-02', 'Critical'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'RE: Defect Rate Exceeding Threshold', 'Dear Team,

We have been notified that shipment SHE-2024-1054 has been held at customs due to regulatory compliance delays. We expect a 16-day delay. This is being resolved and we apologize for the inconvenience.

Wei Chen', '2024-12-15', 'High'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Seasonal Forecast Q1-Q2 2025', 'Dear Procurement,

We are excited to announce our new flame-retardant fabric product line featuring improved specifications and competitive pricing at only 16% premium over standard products.

Best regards,
Rajesh Patel', '2024-12-03', 'Low'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'Shipment Confirmation - CAP-2024-948', 'Dear Supply Chain,

Thank you for your increased order volume. We confirm availability for all requested SKUs. We expect to ship the complete order in a single consolidated shipment arriving by December 21.

Best regards,
James Botha', '2024-12-03', 'Medium'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Express Service Now Available', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 12 days, express option available at 6 days, safety stock maintained at our warehouse.

Best regards,
Rajesh Patel', '2024-12-02', 'Low'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'RE: PO-5054 Shipment Delay Notice', 'Dear Valued Customer,

Due to an unexpected power outage, we must implement a price increase of 9% across affected product lines effective January 21. We understand this is significant and are open to discussing volume-based discounts.

Best regards,
Rajesh Patel', '2025-01-10', 'High'),
(1, 'Pacific Rim Electronics', 'sales@pacificrim.com', 'Express Service Now Available', 'Dear QA Team,

The independent lab results for batch PAC-2024-899 are now available. All samples met or exceeded requirements. We are ready to begin volume production upon your confirmation.

Regards,
Sales', '2024-12-23', 'Low'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Capacity Constraints Notice', 'Hello,

Due to container shortage, our shipping partners have rerouted vessels via alternative routes. This adds approximately 6 days to transit times. We are exploring air freight for urgent orders at 23% cost premium.

Regards,
Rajesh Patel', '2025-01-15', 'High'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'URGENT: Raw Material Price Spike', 'Dear Logistics Team,

We are experiencing quality control issues at our primary warehouse affecting approximately 13% of finished goods. Insurance claims are being filed. We estimate a 11-week delay for affected orders.

Operations Team,
James Botha', '2025-01-06', 'High'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'Force Majeure Declaration', 'Hello,

Following your quality inspection report, we acknowledge that batch CAP-2024-972 had a defect rate of 6.0%, which is above the contractual threshold. The issue was traced to humidity exposure during storage. We have implemented corrective actions and will ship replacements by January 18.

Regards,
James Botha', '2025-01-02', 'Critical'),
(9, 'Yokohama Precision', 'tanaka.h@yokohamaprecision.jp', 'New Product Line Launch', 'Dear Team,

This is to confirm that PO-5044 has been delivered on schedule. All 1000 units passed outgoing quality inspection with a 0.0% defect rate. Please confirm receipt.

Best regards,
Tanaka H', '2024-12-13', 'Low'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'RE: Defect Rate Exceeding Threshold', 'Dear Procurement Team,

We regret to inform you that PO-5053 will be delayed by approximately 20 days. Our factory experienced severe flooding. We are working to resolve this and will provide daily updates.

Best regards,
Rajesh Patel', '2025-01-02', 'High'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'Price Increase Notification', 'Dear Team,

We have been notified that shipment CAP-2024-996 has been held at customs due to regulatory compliance delays. We expect a 9-day delay. This is being resolved and we apologize for the inconvenience.

James Botha', '2024-12-06', 'High'),
(14, 'Guangzhou Textiles', 'lisa.wong@guangzhoutex.cn', 'Quality Certificates - Batch GUA-2024-920', 'Dear QA Team,

The independent lab results for batch GUA-2024-920 are now available. All samples met or exceeded requirements. We are ready to begin volume production upon your confirmation.

Regards,
Lisa Wong', '2024-12-04', 'Low'),
(20, 'Amsterdam BioTech', 'sales@amsterdambiotech.nl', 'Seasonal Forecast Q1-Q2 2025', 'Dear QA Team,

The independent lab results for batch AMS-2024-1117 are now available. All samples met or exceeded requirements. We are ready to begin volume production upon your confirmation.

Regards,
Sales', '2024-12-15', 'Medium'),
(9, 'Yokohama Precision', 'tanaka.h@yokohamaprecision.jp', 'Shipping Route Change Advisory', 'Dear Supply Chain Team,

I am writing to inform you of a critical situation at our facility. labor disputes. This will impact the following open purchase orders: PO-5034 and PO-5030. We are exploring all options including subcontracting.

Sincerely,
Tanaka H', '2024-12-28', 'Medium'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Capacity Constraints Notice', 'Dear Supply Chain Team,

I am writing to inform you of a critical situation at our facility. raw material shortage. This will impact the following open purchase orders: PO-5156 and PO-5036. We are exploring all options including subcontracting.

Sincerely,
Wei Chen', '2024-12-14', 'Medium'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'URGENT: Raw Material Price Spike', 'Hello,

Due to a major equipment failure, our shipping partners have rerouted vessels via alternative routes. This adds approximately 12 days to transit times. We are exploring air freight for urgent orders at 20% cost premium.

Regards,
Wei Chen', '2024-12-31', 'High'),
(16, 'Manchester Fabrics UK', 'orders@manchesterfabrics.uk', 'Annual Quality Report Summary', 'Dear QA Team,

The independent lab results for batch MAN-2024-947 are now available. All samples met or exceeded requirements. We are ready to begin volume production upon your confirmation.

Regards,
Orders', '2024-12-07', 'Low'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Safety Data Sheet Update', 'Dear Team,

This is to confirm that PO-5196 has been delivered on schedule. All 500 units passed outgoing quality inspection with a 0.0% defect rate. Please confirm receipt.

Best regards,
Rajesh Patel', '2024-12-01', 'Low'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Inventory Availability Confirmation', 'Dear QA Team,

The independent lab results for batch MUM-2024-848 are now available. All samples met or exceeded requirements. We are ready to begin volume production upon your confirmation.

Regards,
Rajesh Patel', '2024-12-30', 'Low'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'RE: Missing Documentation for PO-5123', 'Dear Quality Team,

Please find our corrective action report for the port congestion found in batch SHE-2024-905. Root cause analysis identified equipment wear beyond maintenance interval. Corrective actions have been implemented including additional QC checkpoints and staff retraining.

QA Department', '2024-12-01', 'Critical'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'RE: Missing Documentation for PO-5187', 'Dear Supply Chain Team,

I am writing to inform you of a critical situation at our facility. port congestion. This will impact the following open purchase orders: PO-5187 and PO-5044. We are exploring all options including subcontracting.

Sincerely,
Wei Chen', '2024-12-17', 'High'),
(1, 'Pacific Rim Electronics', 'sales@pacificrim.com', 'Express Service Now Available', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Sales', '2024-12-29', 'Low');

INSERT INTO SUPPLIER_EMAILS (SUPPLIER_ID, SUPPLIER_NAME, SENDER, SUBJECT, EMAIL_BODY, DATE_SENT, PRIORITY) VALUES
(19, 'Milan Olive Oil Co.', 'export@milanoliveoil.it', 'Sustainability Initiative Update', 'Dear Team,

This is to confirm that PO-5120 has been delivered on schedule. All 500 units passed outgoing quality inspection with a 0.0% defect rate. Please confirm receipt.

Best regards,
Export', '2024-12-04', 'Low'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'Delayed Shipment Update', 'Dear Quality Team,

Please find our corrective action report for the port congestion found in batch JAK-2024-1084. Root cause analysis identified a calibration error in assembly. Corrective actions have been implemented including additional QC checkpoints and staff retraining.

QA Department', '2024-12-19', 'Critical'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'RE: Partnership Renewal', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Rajesh Patel', '2024-12-25', 'Medium'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'Capacity Constraints Notice', 'Dear Supply Chain Team,

I am writing to inform you of a critical situation at our facility. labor disputes. This will impact the following open purchase orders: PO-5071 and PO-5089. We are exploring all options including subcontracting.

Sincerely,
James Botha', '2024-12-07', 'High'),
(12, 'Toronto Safety Supplies', 'dispatch@torontosafety.ca', 'Technology Upgrade Announcement', 'Dear Purchasing,

Given current market conditions, we would like to offer a price lock arrangement for the next 17 months at favorable rates. Please respond by February 14 to secure these terms.

Regards,
Dispatch', '2025-01-15', 'Medium'),
(8, 'TechnoPlast Brazil', 'carlos.silva@technoplast.br', 'RE: Recurring Quality Complaints', 'Dear Logistics Team,

We are experiencing quality control issues at our primary warehouse affecting approximately 20% of finished goods. Insurance claims are being filed. We estimate a 7-week delay for affected orders.

Operations Team,
Carlos Silva', '2024-12-12', 'High'),
(19, 'Milan Olive Oil Co.', 'export@milanoliveoil.it', 'Lead Time Reduction Update', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 5 days, express option available at 6 days, safety stock maintained at our warehouse.

Best regards,
Export', '2025-01-03', 'Low'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'Quality Certificates - Batch CAP-2024-833', 'Dear Procurement,

We are excited to announce our new eco-friendly cleaning product line featuring improved specifications and competitive pricing at only 20% premium over standard products.

Best regards,
James Botha', '2024-12-29', 'Low'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'Force Majeure Declaration', 'Dear Quality Team,

Please find our corrective action report for the severe flooding found in batch JAK-2024-1074. Root cause analysis identified equipment wear beyond maintenance interval. Corrective actions have been implemented including additional QC checkpoints and staff retraining.

QA Department', '2024-12-31', 'High'),
(1, 'Pacific Rim Electronics', 'sales@pacificrim.com', 'New Product Line Launch', 'Dear Team,

This is to confirm that PO-5017 has been delivered on schedule. All 2500 units passed outgoing quality inspection with a 0.0% defect rate. Please confirm receipt.

Best regards,
Sales', '2025-01-11', 'Medium'),
(6, 'Maple Leaf Foods Inc.', 'supply@mapleleaffoods.ca', 'RE: Partnership Renewal', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Supply', '2025-01-08', 'Low'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'URGENT: Production Line Shutdown', 'Dear Team,

We have been notified that shipment CAP-2024-895 has been held at customs due to raw material shortage. We expect a 6-day delay. This is being resolved and we apologize for the inconvenience.

James Botha', '2024-12-01', 'High'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'Price Increase Notification', 'Dear Team,

We have been notified that shipment CAP-2024-938 has been held at customs due to raw material shortage. We expect a 19-day delay. This is being resolved and we apologize for the inconvenience.

James Botha', '2024-12-23', 'High'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Quality Certificates - Batch SHE-2024-1107', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 21 days, express option available at 5 days, safety stock maintained at our warehouse.

Best regards,
Wei Chen', '2024-12-17', 'Low'),
(5, 'Nordic Steel Works', 'erik.lindqvist@nordicsteel.se', 'Express Service Now Available', 'Dear Partner,

We are pleased to share our Q1 2025 product catalog. As a valued partner, we are offering a 8% early-order discount on orders placed before January 31st. Our production capacity has expanded by 26%.

Warm regards,
Erik Lindqvist', '2024-12-24', 'Low'),
(1, 'Pacific Rim Electronics', 'sales@pacificrim.com', 'Technology Upgrade Announcement', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Sales', '2024-12-24', 'Low'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'Corrective Action Report - CAR-2025-067', 'Dear Quality Team,

Please find our corrective action report for the port congestion found in batch JAK-2024-827. Root cause analysis identified incorrect raw material batch. Corrective actions have been implemented including additional QC checkpoints and staff retraining.

QA Department', '2024-12-16', 'High'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'Sustainability Initiative Update', 'Dear Partner,

We are pleased to share our Q1 2025 product catalog. As a valued partner, we are offering a 19% early-order discount on orders placed before January 31st. Our production capacity has expanded by 29%.

Warm regards,
Siti Rahman', '2024-12-24', 'Low'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'New Product Line Launch', 'Dear QA Team,

The independent lab results for batch SHE-2024-889 are now available. All samples met or exceeded requirements. We are ready to begin volume production upon your confirmation.

Regards,
Wei Chen', '2024-12-23', 'Low'),
(9, 'Yokohama Precision', 'tanaka.h@yokohamaprecision.jp', 'On-Time Delivery Confirmation - PO-5109', 'Dear Supply Chain,

Thank you for your increased order volume. We confirm availability for all requested SKUs. We expect to ship the complete order in a single consolidated shipment arriving by January 30.

Best regards,
Tanaka H', '2025-01-10', 'Low'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Force Majeure Declaration', 'Hello,

Due to raw material shortage, our shipping partners have rerouted vessels via alternative routes. This adds approximately 12 days to transit times. We are exploring air freight for urgent orders at 19% cost premium.

Regards,
Wei Chen', '2025-01-15', 'High'),
(8, 'TechnoPlast Brazil', 'carlos.silva@technoplast.br', 'Annual Quality Report Summary', 'Dear Team,

This is to confirm that PO-5104 has been delivered on schedule. All 500 units passed outgoing quality inspection with a 0.0% defect rate. Please confirm receipt.

Best regards,
Carlos Silva', '2024-12-30', 'Medium'),
(12, 'Toronto Safety Supplies', 'dispatch@torontosafety.ca', 'Sustainability Initiative Update', 'Dear Procurement,

We are excited to announce our new advanced sensor product line featuring improved specifications and competitive pricing at only 5% premium over standard products.

Best regards,
Dispatch', '2025-01-02', 'Medium'),
(19, 'Milan Olive Oil Co.', 'export@milanoliveoil.it', 'Force Majeure Declaration', 'Dear Supply Chain Team,

I am writing to inform you of a critical situation at our facility. port congestion. This will impact the following open purchase orders: PO-5181 and PO-5147. We are exploring all options including subcontracting.

Sincerely,
Export', '2024-12-24', 'High'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Annual Quality Report Summary', 'Dear Supply Chain,

Thank you for your increased order volume. We confirm availability for all requested SKUs. We expect to ship the complete order in a single consolidated shipment arriving by January 29.

Best regards,
Wei Chen', '2025-01-03', 'Low');

INSERT INTO SUPPLIER_EMAILS (SUPPLIER_ID, SUPPLIER_NAME, SENDER, SUBJECT, EMAIL_BODY, DATE_SENT, PRIORITY) VALUES
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'Quality Certificates - Batch CAP-2024-1010', 'Dear Purchasing,

Given current market conditions, we would like to offer a price lock arrangement for the next 20 months at favorable rates. Please respond by January 23 to secure these terms.

Regards,
James Botha', '2025-01-02', 'Low'),
(12, 'Toronto Safety Supplies', 'dispatch@torontosafety.ca', 'Volume Discount Offer 2025', 'Dear Supply Chain,

Thank you for your increased order volume. We confirm availability for all requested SKUs. We expect to ship the complete order in a single consolidated shipment arriving by February 09.

Best regards,
Dispatch', '2025-01-11', 'Low'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Capacity Constraints Notice', 'Dear Quality Team,

Please find our corrective action report for the a major equipment failure found in batch SHE-2024-1096. Root cause analysis identified cross-contamination from adjacent line. Corrective actions have been implemented including additional QC checkpoints and staff retraining.

QA Department', '2024-12-30', 'Critical'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Capacity Constraints Notice', 'Dear Procurement Team,

We regret to inform you that PO-5177 will be delayed by approximately 19 days. Our factory experienced an unexpected power outage. We are working to resolve this and will provide daily updates.

Best regards,
Rajesh Patel', '2024-12-04', 'High'),
(1, 'Pacific Rim Electronics', 'sales@pacificrim.com', 'New Product Line Launch', 'Dear Procurement,

We are excited to announce our new precision bearing product line featuring improved specifications and competitive pricing at only 22% premium over standard products.

Best regards,
Sales', '2024-12-08', 'Low'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Capacity Constraints Notice', 'Dear Logistics Team,

We are experiencing container shortage at our primary warehouse affecting approximately 20% of finished goods. Insurance claims are being filed. We estimate a 5-week delay for affected orders.

Operations Team,
Rajesh Patel', '2025-01-12', 'High'),
(15, 'Santiago Copper Mining', 'exportaciones@santiagocm.cl', 'Inventory Availability Confirmation', 'Dear Purchasing,

Given current market conditions, we would like to offer a price lock arrangement for the next 16 months at favorable rates. Please respond by January 31 to secure these terms.

Regards,
Exportaciones', '2025-01-06', 'Medium'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Express Service Now Available', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 19 days, express option available at 6 days, safety stock maintained at our warehouse.

Best regards,
Rajesh Patel', '2025-01-13', 'Low'),
(5, 'Nordic Steel Works', 'erik.lindqvist@nordicsteel.se', 'Seasonal Forecast Q1-Q2 2025', 'Dear Procurement,

We are excited to announce our new advanced sensor product line featuring improved specifications and competitive pricing at only 10% premium over standard products.

Best regards,
Erik Lindqvist', '2024-12-10', 'Low'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Customs Documentation Error', 'Hello,

Due to regulatory compliance delays, our shipping partners have rerouted vessels via alternative routes. This adds approximately 17 days to transit times. We are exploring air freight for urgent orders at 5% cost premium.

Regards,
Wei Chen', '2024-12-27', 'High'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Q1 2025 Catalog and Early Order Discounts', 'Dear Procurement,

We are excited to announce our new advanced sensor product line featuring improved specifications and competitive pricing at only 15% premium over standard products.

Best regards,
Wei Chen', '2025-01-09', 'Medium'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'Annual Quality Report Summary', 'Dear QA Team,

The independent lab results for batch JAK-2024-1068 are now available. All samples met or exceeded requirements. We are ready to begin volume production upon your confirmation.

Regards,
Siti Rahman', '2024-12-26', 'Low'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'Sustainability Initiative Update', 'Dear Team,

This is to confirm that PO-5006 has been delivered on schedule. All 500 units passed outgoing quality inspection with a 0.0% defect rate. Please confirm receipt.

Best regards,
James Botha', '2025-01-09', 'Low'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Delayed Shipment Update', 'Dear Logistics Team,

We are experiencing container shortage at our primary warehouse affecting approximately 18% of finished goods. Insurance claims are being filed. We estimate a 8-week delay for affected orders.

Operations Team,
Wei Chen', '2025-01-08', 'High'),
(19, 'Milan Olive Oil Co.', 'export@milanoliveoil.it', 'On-Time Delivery Confirmation - PO-5120', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Export', '2024-12-17', 'Low'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'Supply Shortage Alert', 'Dear Logistics Team,

We are experiencing severe flooding at our primary warehouse affecting approximately 10% of finished goods. Insurance claims are being filed. We estimate a 7-week delay for affected orders.

Operations Team,
Siti Rahman', '2024-12-09', 'Medium'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'Annual Quality Report Summary', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Siti Rahman', '2025-01-02', 'Low'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Annual Quality Report Summary', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Wei Chen', '2024-12-07', 'Low'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Capacity Constraints Notice', 'Dear Quality Team,

Please find our corrective action report for the severe flooding found in batch MUM-2024-1166. Root cause analysis identified operator error during shift change. Corrective actions have been implemented including additional QC checkpoints and staff retraining.

QA Department', '2024-12-03', 'Critical'),
(18, 'Seoul Semiconductor', 'park.jh@seoulsemi.kr', 'Express Service Now Available', 'Dear Partner,

We are pleased to share our Q1 2025 product catalog. As a valued partner, we are offering a 10% early-order discount on orders placed before January 31st. Our production capacity has expanded by 29%.

Warm regards,
Park Jh', '2024-12-05', 'Low'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Quality Certificates - Batch SHE-2024-1146', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Wei Chen', '2025-01-01', 'Medium'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'Supply Shortage Alert', 'Hello,

Following your quality inspection report, we acknowledge that batch CAP-2024-1115 had a defect rate of 9.1%, which is above the contractual threshold. The issue was traced to humidity exposure during storage. We have implemented corrective actions and will ship replacements by January 18.

Regards,
James Botha', '2025-01-08', 'High'),
(11, 'Rhine Chemical AG', 'procurement@rhinechemical.de', 'RE: Defect Rate Exceeding Threshold', 'Dear Valued Customer,

Due to container shortage, we must implement a price increase of 23% across affected product lines effective December 30. We understand this is significant and are open to discussing volume-based discounts.

Best regards,
Procurement', '2024-12-11', 'High'),
(1, 'Pacific Rim Electronics', 'sales@pacificrim.com', 'Quality Certificates - Batch PAC-2024-804', 'Dear Procurement,

We are excited to announce our new biodegradable packaging product line featuring improved specifications and competitive pricing at only 13% premium over standard products.

Best regards,
Sales', '2024-12-15', 'Medium'),
(12, 'Toronto Safety Supplies', 'dispatch@torontosafety.ca', 'Lead Time Reduction Update', 'Dear Supply Chain,

Thank you for your increased order volume. We confirm availability for all requested SKUs. We expect to ship the complete order in a single consolidated shipment arriving by January 07.

Best regards,
Dispatch', '2024-12-17', 'Low');

INSERT INTO SUPPLIER_EMAILS (SUPPLIER_ID, SUPPLIER_NAME, SENDER, SUBJECT, EMAIL_BODY, DATE_SENT, PRIORITY) VALUES
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'Supply Shortage Alert', 'Dear Team,

We have been notified that shipment JAK-2024-1151 has been held at customs due to container shortage. We expect a 13-day delay. This is being resolved and we apologize for the inconvenience.

Siti Rahman', '2024-12-24', 'Critical'),
(6, 'Maple Leaf Foods Inc.', 'supply@mapleleaffoods.ca', 'Quality Issue - Batch MAP-2024-900', 'Hello,

Following your quality inspection report, we acknowledge that batch MAP-2024-900 had a defect rate of 7.7%, which is above the contractual threshold. The issue was traced to a calibration error in assembly. We have implemented corrective actions and will ship replacements by January 05.

Regards,
Supply', '2024-12-18', 'High'),
(8, 'TechnoPlast Brazil', 'carlos.silva@technoplast.br', 'Quality Certificates - Batch TEC-2024-882', 'Dear Partner,

We are pleased to share our Q1 2025 product catalog. As a valued partner, we are offering a 13% early-order discount on orders placed before January 31st. Our production capacity has expanded by 27%.

Warm regards,
Carlos Silva', '2025-01-03', 'Medium'),
(15, 'Santiago Copper Mining', 'exportaciones@santiagocm.cl', 'Safety Data Sheet Update', 'Dear Procurement,

We are excited to announce our new flame-retardant fabric product line featuring improved specifications and competitive pricing at only 21% premium over standard products.

Best regards,
Exportaciones', '2025-01-09', 'Low'),
(18, 'Seoul Semiconductor', 'park.jh@seoulsemi.kr', 'Sustainability Initiative Update', 'Dear Procurement,

We are excited to announce our new precision bearing product line featuring improved specifications and competitive pricing at only 25% premium over standard products.

Best regards,
Park Jh', '2024-12-02', 'Medium'),
(2, 'EuroTech Components', 'anna.mueller@eurotech.de', 'Sustainability Initiative Update', 'Dear Purchasing,

Given current market conditions, we would like to offer a price lock arrangement for the next 9 months at favorable rates. Please respond by January 22 to secure these terms.

Regards,
Anna Mueller', '2025-01-04', 'Low'),
(19, 'Milan Olive Oil Co.', 'export@milanoliveoil.it', 'New Product Line Launch', 'Dear Team,

This is to confirm that PO-5098 has been delivered on schedule. All 2500 units passed outgoing quality inspection with a 0.0% defect rate. Please confirm receipt.

Best regards,
Export', '2024-12-25', 'Low'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Annual Quality Report Summary', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 10 days, express option available at 3 days, safety stock maintained at our warehouse.

Best regards,
Rajesh Patel', '2024-12-13', 'Low'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'Inventory Availability Confirmation', 'Dear Partner,

We are pleased to share our Q1 2025 product catalog. As a valued partner, we are offering a 21% early-order discount on orders placed before January 31st. Our production capacity has expanded by 10%.

Warm regards,
James Botha', '2024-12-18', 'Low'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Price Increase Notification', 'Dear Valued Customer,

Due to port congestion, we must implement a price increase of 23% across affected product lines effective December 29. We understand this is significant and are open to discussing volume-based discounts.

Best regards,
Rajesh Patel', '2024-12-08', 'High'),
(3, 'Great Lakes Packaging', 'orders@greatlakespkg.com', 'Inventory Availability Confirmation', 'Dear Partner,

We are pleased to share our Q1 2025 product catalog. As a valued partner, we are offering a 15% early-order discount on orders placed before January 31st. Our production capacity has expanded by 12%.

Warm regards,
Orders', '2024-12-06', 'Medium'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'Customs Documentation Error', 'Dear Supply Chain Team,

I am writing to inform you of a critical situation at our facility. a major equipment failure. This will impact the following open purchase orders: PO-5170 and PO-5019. We are exploring all options including subcontracting.

Sincerely,
James Botha', '2024-12-13', 'Medium'),
(8, 'TechnoPlast Brazil', 'carlos.silva@technoplast.br', 'Technology Upgrade Announcement', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 20 days, express option available at 4 days, safety stock maintained at our warehouse.

Best regards,
Carlos Silva', '2024-12-12', 'Medium'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'RE: Defect Rate Exceeding Threshold', 'Hello,

Following your quality inspection report, we acknowledge that batch CAP-2024-1095 had a defect rate of 3.9%, which is above the contractual threshold. The issue was traced to operator error during shift change. We have implemented corrective actions and will ship replacements by January 18.

Regards,
James Botha', '2024-12-25', 'Critical'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Lead Time Reduction Update', 'Dear Supply Chain,

Thank you for your increased order volume. We confirm availability for all requested SKUs. We expect to ship the complete order in a single consolidated shipment arriving by December 31.

Best regards,
Rajesh Patel', '2024-12-03', 'Low'),
(3, 'Great Lakes Packaging', 'orders@greatlakespkg.com', 'Supply Shortage Alert', 'Hello,

Following your quality inspection report, we acknowledge that batch GRE-2024-1170 had a defect rate of 8.3%, which is above the contractual threshold. The issue was traced to equipment wear beyond maintenance interval. We have implemented corrective actions and will ship replacements by December 27.

Regards,
Orders', '2024-12-03', 'High'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'Seasonal Forecast Q1-Q2 2025', 'Dear Supply Chain,

Thank you for your increased order volume. We confirm availability for all requested SKUs. We expect to ship the complete order in a single consolidated shipment arriving by January 10.

Best regards,
Siti Rahman', '2024-12-16', 'Medium'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'RE: Defect Rate Exceeding Threshold', 'Hello,

Due to regulatory compliance delays, our shipping partners have rerouted vessels via alternative routes. This adds approximately 18 days to transit times. We are exploring air freight for urgent orders at 5% cost premium.

Regards,
Siti Rahman', '2024-12-31', 'High'),
(18, 'Seoul Semiconductor', 'park.jh@seoulsemi.kr', 'Seasonal Forecast Q1-Q2 2025', 'Dear Purchasing,

Given current market conditions, we would like to offer a price lock arrangement for the next 6 months at favorable rates. Please respond by January 29 to secure these terms.

Regards,
Park Jh', '2025-01-05', 'Medium'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Corrective Action Report - CAR-2025-120', 'Dear Quality Team,

Please find our corrective action report for the regulatory compliance delays found in batch SHE-2024-1106. Root cause analysis identified cross-contamination from adjacent line. Corrective actions have been implemented including additional QC checkpoints and staff retraining.

QA Department', '2024-12-03', 'Critical'),
(3, 'Great Lakes Packaging', 'orders@greatlakespkg.com', 'Price Increase Notification', 'Hello,

Following your quality inspection report, we acknowledge that batch GRE-2024-901 had a defect rate of 6.1%, which is above the contractual threshold. The issue was traced to equipment wear beyond maintenance interval. We have implemented corrective actions and will ship replacements by January 01.

Regards,
Orders', '2024-12-19', 'Medium'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'New Product Line Launch', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Rajesh Patel', '2025-01-03', 'Medium'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'RE: Recurring Quality Complaints', 'Dear Supply Chain Team,

I am writing to inform you of a critical situation at our facility. labor disputes. This will impact the following open purchase orders: PO-5058 and PO-5131. We are exploring all options including subcontracting.

Sincerely,
James Botha', '2024-12-23', 'High'),
(8, 'TechnoPlast Brazil', 'carlos.silva@technoplast.br', 'Force Majeure Declaration', 'Dear Valued Customer,

Due to container shortage, we must implement a price increase of 6% across affected product lines effective January 31. We understand this is significant and are open to discussing volume-based discounts.

Best regards,
Carlos Silva', '2025-01-05', 'High'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'On-Time Delivery Confirmation - PO-5139', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 17 days, express option available at 6 days, safety stock maintained at our warehouse.

Best regards,
Wei Chen', '2024-12-09', 'Low');

INSERT INTO SUPPLIER_EMAILS (SUPPLIER_ID, SUPPLIER_NAME, SENDER, SUBJECT, EMAIL_BODY, DATE_SENT, PRIORITY) VALUES
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'Annual Quality Report Summary', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 12 days, express option available at 5 days, safety stock maintained at our warehouse.

Best regards,
Siti Rahman', '2025-01-05', 'Low'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Shipment Confirmation - SHE-2024-1114', 'Dear Purchasing,

Given current market conditions, we would like to offer a price lock arrangement for the next 13 months at favorable rates. Please respond by January 26 to secure these terms.

Regards,
Wei Chen', '2025-01-09', 'Medium'),
(9, 'Yokohama Precision', 'tanaka.h@yokohamaprecision.jp', 'Lead Time Reduction Update', 'Dear Team,

This is to confirm that PO-5053 has been delivered on schedule. All 500 units passed outgoing quality inspection with a 0.0% defect rate. Please confirm receipt.

Best regards,
Tanaka H', '2024-12-19', 'Low'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'URGENT: Production Line Shutdown', 'Dear Logistics Team,

We are experiencing raw material shortage at our primary warehouse affecting approximately 11% of finished goods. Insurance claims are being filed. We estimate a 11-week delay for affected orders.

Operations Team,
Rajesh Patel', '2024-12-01', 'Critical'),
(1, 'Pacific Rim Electronics', 'sales@pacificrim.com', 'Express Service Now Available', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Sales', '2024-12-04', 'Low'),
(11, 'Rhine Chemical AG', 'procurement@rhinechemical.de', 'Price Increase Notification', 'Hello,

Due to port congestion, our shipping partners have rerouted vessels via alternative routes. This adds approximately 10 days to transit times. We are exploring air freight for urgent orders at 22% cost premium.

Regards,
Procurement', '2025-01-06', 'Medium'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'URGENT: Production Line Shutdown', 'Dear Logistics Team,

We are experiencing supply chain disruption at our primary warehouse affecting approximately 5% of finished goods. Insurance claims are being filed. We estimate a 9-week delay for affected orders.

Operations Team,
Wei Chen', '2024-12-10', 'High'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'Quality Certificates - Batch CAP-2024-909', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 21 days, express option available at 4 days, safety stock maintained at our warehouse.

Best regards,
James Botha', '2024-12-17', 'Medium'),
(14, 'Guangzhou Textiles', 'lisa.wong@guangzhoutex.cn', 'Quality Certificates - Batch GUA-2024-1070', 'Dear Procurement,

We are excited to announce our new advanced sensor product line featuring improved specifications and competitive pricing at only 20% premium over standard products.

Best regards,
Lisa Wong', '2025-01-07', 'Low'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'Technology Upgrade Announcement', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 13 days, express option available at 6 days, safety stock maintained at our warehouse.

Best regards,
Siti Rahman', '2024-12-11', 'Low'),
(5, 'Nordic Steel Works', 'erik.lindqvist@nordicsteel.se', 'Seasonal Forecast Q1-Q2 2025', 'Dear Purchasing,

Given current market conditions, we would like to offer a price lock arrangement for the next 16 months at favorable rates. Please respond by January 29 to secure these terms.

Regards,
Erik Lindqvist', '2025-01-15', 'Medium'),
(14, 'Guangzhou Textiles', 'lisa.wong@guangzhoutex.cn', 'Q1 2025 Catalog and Early Order Discounts', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Lisa Wong', '2025-01-09', 'Low'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Force Majeure Declaration', 'Hello,

Following your quality inspection report, we acknowledge that batch MUM-2024-972 had a defect rate of 8.2%, which is above the contractual threshold. The issue was traced to incorrect raw material batch. We have implemented corrective actions and will ship replacements by January 20.

Regards,
Rajesh Patel', '2024-12-30', 'Medium'),
(8, 'TechnoPlast Brazil', 'carlos.silva@technoplast.br', 'Shipment Confirmation - TEC-2024-867', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Carlos Silva', '2024-12-16', 'Medium'),
(6, 'Maple Leaf Foods Inc.', 'supply@mapleleaffoods.ca', 'Technology Upgrade Announcement', 'Dear Procurement,

We are excited to announce our new biodegradable packaging product line featuring improved specifications and competitive pricing at only 19% premium over standard products.

Best regards,
Supply', '2024-12-10', 'Low'),
(16, 'Manchester Fabrics UK', 'orders@manchesterfabrics.uk', 'Express Service Now Available', 'Dear QA Team,

The independent lab results for batch MAN-2024-1145 are now available. All samples met or exceeded requirements. We are ready to begin volume production upon your confirmation.

Regards,
Orders', '2024-12-05', 'Medium'),
(16, 'Manchester Fabrics UK', 'orders@manchesterfabrics.uk', 'Volume Discount Offer 2025', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 6 days, express option available at 5 days, safety stock maintained at our warehouse.

Best regards,
Orders', '2025-01-13', 'Medium'),
(14, 'Guangzhou Textiles', 'lisa.wong@guangzhoutex.cn', 'RE: Partnership Renewal', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Lisa Wong', '2024-12-26', 'Low'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'Force Majeure Declaration', 'Dear Logistics Team,

We are experiencing quality control issues at our primary warehouse affecting approximately 13% of finished goods. Insurance claims are being filed. We estimate a 17-week delay for affected orders.

Operations Team,
James Botha', '2025-01-11', 'High'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'RE: Recurring Quality Complaints', 'Dear Valued Customer,

Due to severe flooding, we must implement a price increase of 11% across affected product lines effective January 16. We understand this is significant and are open to discussing volume-based discounts.

Best regards,
Wei Chen', '2025-01-02', 'Medium'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'RE: PO-5111 Shipment Delay Notice', 'Dear Team,

We have been notified that shipment CAP-2024-1132 has been held at customs due to severe flooding. We expect a 7-day delay. This is being resolved and we apologize for the inconvenience.

James Botha', '2024-12-19', 'High'),
(8, 'TechnoPlast Brazil', 'carlos.silva@technoplast.br', 'Technology Upgrade Announcement', 'Dear Team,

This is to confirm that PO-5110 has been delivered on schedule. All 200 units passed outgoing quality inspection with a 0.0% defect rate. Please confirm receipt.

Best regards,
Carlos Silva', '2025-01-05', 'Low'),
(1, 'Pacific Rim Electronics', 'sales@pacificrim.com', 'Quality Certificates - Batch PAC-2024-946', 'Dear Purchasing,

Given current market conditions, we would like to offer a price lock arrangement for the next 12 months at favorable rates. Please respond by February 01 to secure these terms.

Regards,
Sales', '2025-01-12', 'Medium'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Corrective Action Report - CAR-2025-149', 'Hello,

Due to a major equipment failure, our shipping partners have rerouted vessels via alternative routes. This adds approximately 11 days to transit times. We are exploring air freight for urgent orders at 7% cost premium.

Regards,
Wei Chen', '2024-12-21', 'High'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'Shipment Confirmation - JAK-2024-1125', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 10 days, express option available at 3 days, safety stock maintained at our warehouse.

Best regards,
Siti Rahman', '2025-01-11', 'Medium');

INSERT INTO SUPPLIER_EMAILS (SUPPLIER_ID, SUPPLIER_NAME, SENDER, SUBJECT, EMAIL_BODY, DATE_SENT, PRIORITY) VALUES
(11, 'Rhine Chemical AG', 'procurement@rhinechemical.de', 'Quality Certificates - Batch RHI-2024-1099', 'Dear Procurement,

We are excited to announce our new biodegradable packaging product line featuring improved specifications and competitive pricing at only 23% premium over standard products.

Best regards,
Procurement', '2024-12-16', 'Low'),
(16, 'Manchester Fabrics UK', 'orders@manchesterfabrics.uk', 'On-Time Delivery Confirmation - PO-5118', 'Dear Purchasing,

Given current market conditions, we would like to offer a price lock arrangement for the next 13 months at favorable rates. Please respond by January 31 to secure these terms.

Regards,
Orders', '2025-01-12', 'Low'),
(5, 'Nordic Steel Works', 'erik.lindqvist@nordicsteel.se', 'Seasonal Forecast Q1-Q2 2025', 'Dear Supply Chain,

Thank you for your increased order volume. We confirm availability for all requested SKUs. We expect to ship the complete order in a single consolidated shipment arriving by January 22.

Best regards,
Erik Lindqvist', '2025-01-10', 'Low'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'Quality Issue - Batch CAP-2024-979', 'Hello,

Following your quality inspection report, we acknowledge that batch CAP-2024-979 had a defect rate of 9.5%, which is above the contractual threshold. The issue was traced to cross-contamination from adjacent line. We have implemented corrective actions and will ship replacements by December 27.

Regards,
James Botha', '2024-12-13', 'Medium'),
(5, 'Nordic Steel Works', 'erik.lindqvist@nordicsteel.se', 'Annual Quality Report Summary', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 7 days, express option available at 4 days, safety stock maintained at our warehouse.

Best regards,
Erik Lindqvist', '2025-01-14', 'Low'),
(8, 'TechnoPlast Brazil', 'carlos.silva@technoplast.br', 'Q1 2025 Catalog and Early Order Discounts', 'Dear Partner,

We are pleased to share our Q1 2025 product catalog. As a valued partner, we are offering a 11% early-order discount on orders placed before January 31st. Our production capacity has expanded by 24%.

Warm regards,
Carlos Silva', '2024-12-31', 'Low'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Technology Upgrade Announcement', 'Dear QA Team,

The independent lab results for batch MUM-2024-975 are now available. All samples met or exceeded requirements. We are ready to begin volume production upon your confirmation.

Regards,
Rajesh Patel', '2024-12-27', 'Low'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Customs Documentation Error', 'Dear Valued Customer,

Due to quality control issues, we must implement a price increase of 9% across affected product lines effective January 05. We understand this is significant and are open to discussing volume-based discounts.

Best regards,
Rajesh Patel', '2024-12-15', 'High'),
(18, 'Seoul Semiconductor', 'park.jh@seoulsemi.kr', 'Supply Shortage Alert', 'Dear Team,

We have been notified that shipment SEO-2024-1135 has been held at customs due to container shortage. We expect a 16-day delay. This is being resolved and we apologize for the inconvenience.

Park Jh', '2025-01-05', 'Critical'),
(9, 'Yokohama Precision', 'tanaka.h@yokohamaprecision.jp', 'Volume Discount Offer 2025', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Tanaka H', '2024-12-13', 'Low'),
(8, 'TechnoPlast Brazil', 'carlos.silva@technoplast.br', 'URGENT: Raw Material Price Spike', 'Dear Valued Customer,

Due to labor disputes, we must implement a price increase of 25% across affected product lines effective December 31. We understand this is significant and are open to discussing volume-based discounts.

Best regards,
Carlos Silva', '2024-12-17', 'Critical'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Capacity Constraints Notice', 'Hello,

Following your quality inspection report, we acknowledge that batch MUM-2024-941 had a defect rate of 3.5%, which is above the contractual threshold. The issue was traced to a calibration error in assembly. We have implemented corrective actions and will ship replacements by January 23.

Regards,
Rajesh Patel', '2025-01-08', 'Critical'),
(12, 'Toronto Safety Supplies', 'dispatch@torontosafety.ca', 'New Product Line Launch', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 9 days, express option available at 7 days, safety stock maintained at our warehouse.

Best regards,
Dispatch', '2024-12-30', 'Low'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'Price Increase Notification', 'Dear Valued Customer,

Due to regulatory compliance delays, we must implement a price increase of 9% across affected product lines effective January 25. We understand this is significant and are open to discussing volume-based discounts.

Best regards,
Siti Rahman', '2024-12-29', 'Critical'),
(15, 'Santiago Copper Mining', 'exportaciones@santiagocm.cl', 'On-Time Delivery Confirmation - PO-5123', 'Dear Team,

This is to confirm that PO-5123 has been delivered on schedule. All 200 units passed outgoing quality inspection with a 0.0% defect rate. Please confirm receipt.

Best regards,
Exportaciones', '2025-01-14', 'Low'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Customs Documentation Error', 'Dear Procurement Team,

We regret to inform you that PO-5068 will be delayed by approximately 15 days. Our factory experienced supply chain disruption. We are working to resolve this and will provide daily updates.

Best regards,
Wei Chen', '2025-01-09', 'Medium'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'RE: PO-5093 Shipment Delay Notice', 'Dear Team,

We have been notified that shipment SHE-2024-979 has been held at customs due to raw material shortage. We expect a 11-day delay. This is being resolved and we apologize for the inconvenience.

Wei Chen', '2024-12-10', 'Critical'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'Customs Documentation Error', 'Dear Logistics Team,

We are experiencing supply chain disruption at our primary warehouse affecting approximately 17% of finished goods. Insurance claims are being filed. We estimate a 17-week delay for affected orders.

Operations Team,
Siti Rahman', '2024-12-13', 'Medium'),
(1, 'Pacific Rim Electronics', 'sales@pacificrim.com', 'Annual Quality Report Summary', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Sales', '2025-01-09', 'Low'),
(2, 'EuroTech Components', 'anna.mueller@eurotech.de', 'URGENT: Raw Material Price Spike', 'Dear Quality Team,

Please find our corrective action report for the a major equipment failure found in batch EUR-2024-818. Root cause analysis identified equipment wear beyond maintenance interval. Corrective actions have been implemented including additional QC checkpoints and staff retraining.

QA Department', '2024-12-17', 'Medium'),
(11, 'Rhine Chemical AG', 'procurement@rhinechemical.de', 'Lead Time Reduction Update', 'Dear QA Team,

The independent lab results for batch RHI-2024-955 are now available. All samples met or exceeded requirements. We are ready to begin volume production upon your confirmation.

Regards,
Procurement', '2024-12-01', 'Low'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'RE: Defect Rate Exceeding Threshold', 'Dear Team,

We have been notified that shipment JAK-2024-1092 has been held at customs due to a major equipment failure. We expect a 12-day delay. This is being resolved and we apologize for the inconvenience.

Siti Rahman', '2025-01-15', 'Critical'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'Quality Certificates - Batch JAK-2024-848', 'Dear Procurement,

We are excited to announce our new high-efficiency LED product line featuring improved specifications and competitive pricing at only 11% premium over standard products.

Best regards,
Siti Rahman', '2024-12-09', 'Low'),
(16, 'Manchester Fabrics UK', 'orders@manchesterfabrics.uk', 'New Product Line Launch', 'Dear Partner,

We are pleased to share our Q1 2025 product catalog. As a valued partner, we are offering a 8% early-order discount on orders placed before January 31st. Our production capacity has expanded by 28%.

Warm regards,
Orders', '2024-12-17', 'Low'),
(2, 'EuroTech Components', 'anna.mueller@eurotech.de', 'Customs Documentation Error', 'Dear Logistics Team,

We are experiencing quality control issues at our primary warehouse affecting approximately 6% of finished goods. Insurance claims are being filed. We estimate a 6-week delay for affected orders.

Operations Team,
Anna Mueller', '2024-12-25', 'High');

INSERT INTO SUPPLIER_EMAILS (SUPPLIER_ID, SUPPLIER_NAME, SENDER, SUBJECT, EMAIL_BODY, DATE_SENT, PRIORITY) VALUES
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'RE: Missing Documentation for PO-5056', 'Dear Supply Chain Team,

I am writing to inform you of a critical situation at our facility. labor disputes. This will impact the following open purchase orders: PO-5056 and PO-5091. We are exploring all options including subcontracting.

Sincerely,
Siti Rahman', '2024-12-07', 'High'),
(2, 'EuroTech Components', 'anna.mueller@eurotech.de', 'RE: PO-5001 Shipment Delay Notice', 'Dear Supply Chain Team,

I am writing to inform you of a critical situation at our facility. a major equipment failure. This will impact the following open purchase orders: PO-5001 and PO-5009. We are exploring all options including subcontracting.

Sincerely,
Anna Mueller', '2024-12-06', 'High'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Customs Documentation Error', 'Dear Logistics Team,

We are experiencing container shortage at our primary warehouse affecting approximately 16% of finished goods. Insurance claims are being filed. We estimate a 19-week delay for affected orders.

Operations Team,
Rajesh Patel', '2025-01-01', 'Critical'),
(12, 'Toronto Safety Supplies', 'dispatch@torontosafety.ca', 'Technology Upgrade Announcement', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Dispatch', '2024-12-20', 'Medium'),
(1, 'Pacific Rim Electronics', 'sales@pacificrim.com', 'Safety Data Sheet Update', 'Dear Supply Chain,

Thank you for your increased order volume. We confirm availability for all requested SKUs. We expect to ship the complete order in a single consolidated shipment arriving by January 16.

Best regards,
Sales', '2025-01-02', 'Low'),
(6, 'Maple Leaf Foods Inc.', 'supply@mapleleaffoods.ca', 'Safety Data Sheet Update', 'Dear Supply Chain,

Thank you for your increased order volume. We confirm availability for all requested SKUs. We expect to ship the complete order in a single consolidated shipment arriving by January 04.

Best regards,
Supply', '2024-12-25', 'Low'),
(1, 'Pacific Rim Electronics', 'sales@pacificrim.com', 'RE: Recurring Quality Complaints', 'Dear Supply Chain Team,

I am writing to inform you of a critical situation at our facility. container shortage. This will impact the following open purchase orders: PO-5085 and PO-5120. We are exploring all options including subcontracting.

Sincerely,
Sales', '2025-01-02', 'Critical'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'RE: Missing Documentation for PO-5074', 'Dear Supply Chain Team,

I am writing to inform you of a critical situation at our facility. severe flooding. This will impact the following open purchase orders: PO-5074 and PO-5147. We are exploring all options including subcontracting.

Sincerely,
Rajesh Patel', '2024-12-10', 'Critical'),
(18, 'Seoul Semiconductor', 'park.jh@seoulsemi.kr', 'On-Time Delivery Confirmation - PO-5189', 'Dear QA Team,

The independent lab results for batch SEO-2024-1016 are now available. All samples met or exceeded requirements. We are ready to begin volume production upon your confirmation.

Regards,
Park Jh', '2024-12-23', 'Low'),
(3, 'Great Lakes Packaging', 'orders@greatlakespkg.com', 'Volume Discount Offer 2025', 'Dear Procurement,

We are excited to announce our new eco-friendly cleaning product line featuring improved specifications and competitive pricing at only 22% premium over standard products.

Best regards,
Orders', '2025-01-07', 'Low'),
(6, 'Maple Leaf Foods Inc.', 'supply@mapleleaffoods.ca', 'Lead Time Reduction Update', 'Dear Health & Safety Team,

We have updated Safety Data Sheets for our products in compliance with latest regulations. No changes to product composition - documentation updates only. New SDS documents are attached.

Regards,
Supply', '2025-01-08', 'Low'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'Technology Upgrade Announcement', 'Dear Procurement,

We are excited to announce our new high-efficiency LED product line featuring improved specifications and competitive pricing at only 8% premium over standard products.

Best regards,
Wei Chen', '2024-12-04', 'Medium'),
(18, 'Seoul Semiconductor', 'park.jh@seoulsemi.kr', 'New Product Line Launch', 'Dear Supply Chain,

Thank you for your increased order volume. We confirm availability for all requested SKUs. We expect to ship the complete order in a single consolidated shipment arriving by January 15.

Best regards,
Park Jh', '2024-12-28', 'Low'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Shipping Route Change Advisory', 'Dear Supply Chain Team,

I am writing to inform you of a critical situation at our facility. container shortage. This will impact the following open purchase orders: PO-5070 and PO-5038. We are exploring all options including subcontracting.

Sincerely,
Rajesh Patel', '2025-01-04', 'Medium'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Force Majeure Declaration', 'Dear Quality Team,

Please find our corrective action report for the an unexpected power outage found in batch MUM-2024-1109. Root cause analysis identified operator error during shift change. Corrective actions have been implemented including additional QC checkpoints and staff retraining.

QA Department', '2024-12-04', 'Critical'),
(1, 'Pacific Rim Electronics', 'sales@pacificrim.com', 'New Product Line Launch', 'Dear QA Team,

The independent lab results for batch PAC-2024-1187 are now available. All samples met or exceeded requirements. We are ready to begin volume production upon your confirmation.

Regards,
Sales', '2024-12-05', 'Low'),
(7, 'Mumbai Industrial Co.', 'rajesh.patel@mumbaiindustrial.in', 'Volume Discount Offer 2025', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 10 days, express option available at 4 days, safety stock maintained at our warehouse.

Best regards,
Rajesh Patel', '2025-01-12', 'Low'),
(17, 'Cape Town Trading', 'james.botha@capetowntrading.za', 'Price Increase Notification', 'Dear Supply Chain Team,

I am writing to inform you of a critical situation at our facility. quality control issues. This will impact the following open purchase orders: PO-5065 and PO-5064. We are exploring all options including subcontracting.

Sincerely,
James Botha', '2024-12-06', 'High'),
(11, 'Rhine Chemical AG', 'procurement@rhinechemical.de', 'On-Time Delivery Confirmation - PO-5186', 'Dear QA Team,

The independent lab results for batch RHI-2024-1061 are now available. All samples met or exceeded requirements. We are ready to begin volume production upon your confirmation.

Regards,
Procurement', '2024-12-03', 'Low'),
(11, 'Rhine Chemical AG', 'procurement@rhinechemical.de', 'New Product Line Launch', 'Dear Partner,

We are pleased to share our Q1 2025 product catalog. As a valued partner, we are offering a 9% early-order discount on orders placed before January 31st. Our production capacity has expanded by 28%.

Warm regards,
Procurement', '2024-12-12', 'Low'),
(9, 'Yokohama Precision', 'tanaka.h@yokohamaprecision.jp', 'Technology Upgrade Announcement', 'Dear Supply Chain,

Thank you for your increased order volume. We confirm availability for all requested SKUs. We expect to ship the complete order in a single consolidated shipment arriving by January 30.

Best regards,
Tanaka H', '2025-01-13', 'Low'),
(4, 'Shenzhen Fast Supply', 'wei.chen@shenzhenfast.cn', 'New Product Line Launch', 'Dear Purchasing,

Given current market conditions, we would like to offer a price lock arrangement for the next 13 months at favorable rates. Please respond by January 16 to secure these terms.

Regards,
Wei Chen', '2024-12-19', 'Low'),
(13, 'Jakarta Industrial Hub', 'siti.rahman@jakartahub.id', 'RE: Recurring Quality Complaints', 'Dear Supply Chain Team,

I am writing to inform you of a critical situation at our facility. regulatory compliance delays. This will impact the following open purchase orders: PO-5183 and PO-5180. We are exploring all options including subcontracting.

Sincerely,
Siti Rahman', '2024-12-02', 'Medium'),
(5, 'Nordic Steel Works', 'erik.lindqvist@nordicsteel.se', 'Inventory Availability Confirmation', 'Dear Procurement,

We are excited to announce our new high-efficiency LED product line featuring improved specifications and competitive pricing at only 10% premium over standard products.

Best regards,
Erik Lindqvist', '2024-12-13', 'Medium'),
(5, 'Nordic Steel Works', 'erik.lindqvist@nordicsteel.se', 'Q1 2025 Catalog and Early Order Discounts', 'Dear Partner,

Thank you for your continued partnership. We confirm the following improvements: standard lead time reduced to 11 days, express option available at 5 days, safety stock maintained at our warehouse.

Best regards,
Erik Lindqvist', '2024-12-21', 'Low');

-- ============================================================
-- WAREHOUSE_INSPECTION_NOTES (170 rows)
-- ============================================================

INSERT INTO WAREHOUSE_INSPECTION_NOTES (WAREHOUSE_ID, WAREHOUSE_NAME, INSPECTION_DATE, INSPECTOR, OVERALL_RATING, FOLLOW_UP_REQUIRED, INSPECTION_NOTES) VALUES
(1, 'West Coast Hub', '2024-11-13', 'James Rodriguez', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: November 13, 2024
Inspector: James Rodriguez

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: Safety signage visible and up to date in all zones.

FOLLOW-UP REQUIRED:
- Install additional security cameras.
- Repaint fading floor markings.'),
(2, 'Midwest Distribution', '2024-11-06', 'Patricia Evans', 'Poor', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: November 06, 2024
Inspector: Patricia Evans

OVERALL RATING: POOR

Significant deficiencies identified. Mandatory follow-up inspection required.

SAFETY: Safety signage visible and up to date in all zones.

FOLLOW-UP REQUIRED:
- Address humidity control issues.
- Update emergency procedures documentation.'),
(3, 'East Coast Fulfillment', '2024-10-31', 'Patricia Evans', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: October 31, 2024
Inspector: Patricia Evans

OVERALL RATING: GOOD

Generally well-maintained facility. Minor observations noted for routine follow-up.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(4, 'Southeast Logistics', '2024-10-31', 'Patricia Evans', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: October 31, 2024
Inspector: Patricia Evans

OVERALL RATING: GOOD

Facility in good condition. Inventory accuracy high and receiving processes efficient.

SAFETY: First aid stations fully stocked. AED units tested and operational.'),
(5, 'Texas Mega Center', '2024-12-10', 'Patricia Evans', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: December 10, 2024
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: Spill kits present and fully stocked at all hazmat locations.

FOLLOW-UP REQUIRED:
- Schedule pest control follow-up treatment.
- Enforce maximum pallet stack height limits.'),
(6, 'Pacific Northwest Depot', '2024-11-05', 'Maria Santos', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: November 05, 2024
Inspector: Maria Santos

OVERALL RATING: SATISFACTORY

Satisfactory overall but housekeeping standards inconsistent between shifts.

SAFETY: Forklift daily inspection logs complete and current.'),
(7, 'Mountain West Facility', '2024-12-29', 'Maria Santos', 'Poor', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: December 29, 2024
Inspector: Maria Santos

OVERALL RATING: POOR

Below acceptable standards. Equipment maintenance overdue and safety violations found.

SAFETY: Spill kits present and fully stocked at all hazmat locations.

FOLLOW-UP REQUIRED:
- Replace failed emergency lighting units.
- Schedule pest control follow-up treatment.'),
(8, 'Florida Gateway', '2024-10-30', 'Maria Santos', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: October 30, 2024
Inspector: Maria Santos

OVERALL RATING: GOOD

Facility in good condition. Inventory accuracy high and receiving processes efficient.

SAFETY: Safety signage visible and up to date in all zones.'),
(1, 'West Coast Hub', '2025-01-02', 'James Rodriguez', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: January 02, 2025
Inspector: James Rodriguez

OVERALL RATING: EXCELLENT

All zones passed inspection with no findings. Aisles clear, racking in excellent condition.

SAFETY: Safety signage visible and up to date in all zones.'),
(2, 'Midwest Distribution', '2024-12-07', 'Patricia Evans', 'Critical', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: December 07, 2024
Inspector: Patricia Evans

OVERALL RATING: CRITICAL

CRITICAL: Facility does not meet minimum safety and operational standards.

SAFETY: Emergency lighting tested - all units operational.

FOLLOW-UP REQUIRED:
- Schedule pest control follow-up treatment.
- Repaint fading floor markings.'),
(3, 'East Coast Fulfillment', '2024-11-13', 'Sarah Chen', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: November 13, 2024
Inspector: Sarah Chen

OVERALL RATING: SATISFACTORY

Satisfactory overall but housekeeping standards inconsistent between shifts.

SAFETY: Forklift daily inspection logs complete and current.'),
(4, 'Southeast Logistics', '2025-01-05', 'Maria Santos', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: January 05, 2025
Inspector: Maria Santos

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: Spill kits present and fully stocked at all hazmat locations.

FOLLOW-UP REQUIRED:
- Schedule pest control follow-up treatment.'),
(5, 'Texas Mega Center', '2024-11-04', 'James Rodriguez', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: November 04, 2024
Inspector: James Rodriguez

OVERALL RATING: SATISFACTORY

Acceptable conditions with some areas requiring attention within 30 days.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.

FOLLOW-UP REQUIRED:
- Replace deteriorating dock door seal.
- Repaint fading floor markings.'),
(6, 'Pacific Northwest Depot', '2025-01-09', 'David Kim', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: January 09, 2025
Inspector: David Kim

OVERALL RATING: SATISFACTORY

Acceptable conditions with some areas requiring attention within 30 days.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(7, 'Mountain West Facility', '2024-12-12', 'Maria Santos', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: December 12, 2024
Inspector: Maria Santos

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.'),
(8, 'Florida Gateway', '2024-10-19', 'Sarah Chen', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: October 19, 2024
Inspector: Sarah Chen

OVERALL RATING: SATISFACTORY

Acceptable conditions with some areas requiring attention within 30 days.

SAFETY: First aid stations fully stocked. AED units tested and operational.'),
(1, 'West Coast Hub', '2024-10-31', 'Sarah Chen', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: October 31, 2024
Inspector: Sarah Chen

OVERALL RATING: SATISFACTORY

Satisfactory overall but housekeeping standards inconsistent between shifts.

SAFETY: First aid stations fully stocked. AED units tested and operational.'),
(2, 'Midwest Distribution', '2024-12-04', 'Patricia Evans', 'Poor', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: December 04, 2024
Inspector: Patricia Evans

OVERALL RATING: POOR

Below acceptable standards. Equipment maintenance overdue and safety violations found.

SAFETY: PPE compliance observed at 95% during walkthrough.

FOLLOW-UP REQUIRED:
- Replace failed emergency lighting units.'),
(3, 'East Coast Fulfillment', '2024-11-12', 'David Kim', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: November 12, 2024
Inspector: David Kim

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.'),
(4, 'Southeast Logistics', '2024-11-02', 'Sarah Chen', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: November 02, 2024
Inspector: Sarah Chen

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: PPE compliance observed at 95% during walkthrough.

FOLLOW-UP REQUIRED:
- Enforce maximum pallet stack height limits.
- Repair HVAC system in affected zone.');

INSERT INTO WAREHOUSE_INSPECTION_NOTES (WAREHOUSE_ID, WAREHOUSE_NAME, INSPECTION_DATE, INSPECTOR, OVERALL_RATING, FOLLOW_UP_REQUIRED, INSPECTION_NOTES) VALUES
(5, 'Texas Mega Center', '2024-11-24', 'David Kim', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: November 24, 2024
Inspector: David Kim

OVERALL RATING: GOOD

Good overall condition. Temperature and humidity within specifications across all zones.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(6, 'Pacific Northwest Depot', '2025-01-01', 'David Kim', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: January 01, 2025
Inspector: David Kim

OVERALL RATING: EXCELLENT

Model facility - recommended as benchmark. Inventory organization is exemplary.

SAFETY: First aid stations fully stocked. AED units tested and operational.'),
(7, 'Mountain West Facility', '2024-10-17', 'Patricia Evans', 'Poor', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: October 17, 2024
Inspector: Patricia Evans

OVERALL RATING: POOR

Multiple critical findings requiring immediate corrective action within 14 days.

SAFETY: Safety signage visible and up to date in all zones.

FOLLOW-UP REQUIRED:
- Complete overdue equipment calibration.'),
(8, 'Florida Gateway', '2024-11-16', 'James Rodriguez', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: November 16, 2024
Inspector: James Rodriguez

OVERALL RATING: SATISFACTORY

Satisfactory overall but housekeeping standards inconsistent between shifts.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(1, 'West Coast Hub', '2025-01-02', 'Patricia Evans', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: January 02, 2025
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.'),
(2, 'Midwest Distribution', '2024-12-20', 'Maria Santos', 'Critical', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: December 20, 2024
Inspector: Maria Santos

OVERALL RATING: CRITICAL

CRITICAL FAILURE: Core infrastructure systems non-functional. Operations at risk.

SAFETY: Forklift daily inspection logs complete and current.

FOLLOW-UP REQUIRED:
- Repair HVAC system in affected zone.'),
(3, 'East Coast Fulfillment', '2024-12-30', 'Maria Santos', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: December 30, 2024
Inspector: Maria Santos

OVERALL RATING: GOOD

Facility in good condition. Inventory accuracy high and receiving processes efficient.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(4, 'Southeast Logistics', '2024-10-18', 'David Kim', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: October 18, 2024
Inspector: David Kim

OVERALL RATING: SATISFACTORY

Acceptable conditions with some areas requiring attention within 30 days.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(5, 'Texas Mega Center', '2024-11-13', 'David Kim', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: November 13, 2024
Inspector: David Kim

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: Safety signage visible and up to date in all zones.'),
(6, 'Pacific Northwest Depot', '2024-12-18', 'David Kim', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: December 18, 2024
Inspector: David Kim

OVERALL RATING: GOOD

Strong operational controls observed. Staff knowledgeable about emergency procedures.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.'),
(7, 'Mountain West Facility', '2024-11-14', 'James Rodriguez', 'Poor', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: November 14, 2024
Inspector: James Rodriguez

OVERALL RATING: POOR

Below acceptable standards. Equipment maintenance overdue and safety violations found.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.

FOLLOW-UP REQUIRED:
- Repair HVAC system in affected zone.
- Replace deteriorating dock door seal.
- Enforce maximum pallet stack height limits.'),
(8, 'Florida Gateway', '2024-12-15', 'Patricia Evans', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: December 15, 2024
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Acceptable conditions with some areas requiring attention within 30 days.

SAFETY: First aid stations fully stocked. AED units tested and operational.'),
(1, 'West Coast Hub', '2024-11-06', 'Patricia Evans', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: November 06, 2024
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: First aid stations fully stocked. AED units tested and operational.'),
(2, 'Midwest Distribution', '2024-12-22', 'James Rodriguez', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: December 22, 2024
Inspector: James Rodriguez

OVERALL RATING: SATISFACTORY

Satisfactory overall but housekeeping standards inconsistent between shifts.

SAFETY: Emergency lighting tested - all units operational.

FOLLOW-UP REQUIRED:
- Schedule pest control follow-up treatment.
- Install additional security cameras.
- Update emergency procedures documentation.'),
(3, 'East Coast Fulfillment', '2024-12-07', 'Patricia Evans', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: December 07, 2024
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(4, 'Southeast Logistics', '2024-10-07', 'Maria Santos', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: October 07, 2024
Inspector: Maria Santos

OVERALL RATING: EXCELLENT

All zones passed inspection with no findings. Aisles clear, racking in excellent condition.

SAFETY: Emergency lighting tested - all units operational.'),
(5, 'Texas Mega Center', '2025-01-03', 'Patricia Evans', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: January 03, 2025
Inspector: Patricia Evans

OVERALL RATING: GOOD

Facility in good condition. Inventory accuracy high and receiving processes efficient.

SAFETY: Forklift daily inspection logs complete and current.'),
(6, 'Pacific Northwest Depot', '2024-12-31', 'David Kim', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: December 31, 2024
Inspector: David Kim

OVERALL RATING: GOOD

Facility in good condition. Inventory accuracy high and receiving processes efficient.

SAFETY: First aid stations fully stocked. AED units tested and operational.'),
(7, 'Mountain West Facility', '2024-11-27', 'David Kim', 'Critical', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: November 27, 2024
Inspector: David Kim

OVERALL RATING: CRITICAL

URGENT: Multiple life-safety violations requiring immediate remediation.

SAFETY: Forklift daily inspection logs complete and current.

FOLLOW-UP REQUIRED:
- Update emergency procedures documentation.
- Address humidity control issues.'),
(8, 'Florida Gateway', '2025-01-01', 'David Kim', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: January 01, 2025
Inspector: David Kim

OVERALL RATING: GOOD

Good overall condition. Temperature and humidity within specifications across all zones.

SAFETY: First aid stations fully stocked. AED units tested and operational.');

INSERT INTO WAREHOUSE_INSPECTION_NOTES (WAREHOUSE_ID, WAREHOUSE_NAME, INSPECTION_DATE, INSPECTOR, OVERALL_RATING, FOLLOW_UP_REQUIRED, INSPECTION_NOTES) VALUES
(1, 'West Coast Hub', '2024-10-21', 'James Rodriguez', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: October 21, 2024
Inspector: James Rodriguez

OVERALL RATING: GOOD

Strong operational controls observed. Staff knowledgeable about emergency procedures.

SAFETY: First aid stations fully stocked. AED units tested and operational.'),
(2, 'Midwest Distribution', '2024-12-16', 'Sarah Chen', 'Critical', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: December 16, 2024
Inspector: Sarah Chen

OVERALL RATING: CRITICAL

CRITICAL FAILURE: Core infrastructure systems non-functional. Operations at risk.

SAFETY: Safety signage visible and up to date in all zones.

FOLLOW-UP REQUIRED:
- Schedule pest control follow-up treatment.
- Replace failed emergency lighting units.'),
(3, 'East Coast Fulfillment', '2024-12-11', 'Sarah Chen', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: December 11, 2024
Inspector: Sarah Chen

OVERALL RATING: EXCELLENT

All zones passed inspection with no findings. Aisles clear, racking in excellent condition.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.'),
(4, 'Southeast Logistics', '2024-10-24', 'Maria Santos', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: October 24, 2024
Inspector: Maria Santos

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(5, 'Texas Mega Center', '2024-11-05', 'Maria Santos', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: November 05, 2024
Inspector: Maria Santos

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(6, 'Pacific Northwest Depot', '2024-11-12', 'Maria Santos', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: November 12, 2024
Inspector: Maria Santos

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: Spill kits present and fully stocked at all hazmat locations.

FOLLOW-UP REQUIRED:
- Complete overdue equipment calibration.
- Repaint fading floor markings.
- Update emergency procedures documentation.'),
(7, 'Mountain West Facility', '2024-11-28', 'Maria Santos', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: November 28, 2024
Inspector: Maria Santos

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: Safety signage visible and up to date in all zones.'),
(8, 'Florida Gateway', '2025-01-04', 'James Rodriguez', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: January 04, 2025
Inspector: James Rodriguez

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.'),
(1, 'West Coast Hub', '2024-10-17', 'Maria Santos', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: October 17, 2024
Inspector: Maria Santos

OVERALL RATING: GOOD

Facility in good condition. Inventory accuracy high and receiving processes efficient.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(2, 'Midwest Distribution', '2024-11-27', 'Patricia Evans', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: November 27, 2024
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: First aid stations fully stocked. AED units tested and operational.

FOLLOW-UP REQUIRED:
- Repaint fading floor markings.
- Replace failed emergency lighting units.
- Install additional security cameras.'),
(3, 'East Coast Fulfillment', '2024-12-30', 'Maria Santos', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: December 30, 2024
Inspector: Maria Santos

OVERALL RATING: GOOD

Good overall condition. Temperature and humidity within specifications across all zones.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(4, 'Southeast Logistics', '2024-11-05', 'Maria Santos', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: November 05, 2024
Inspector: Maria Santos

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(5, 'Texas Mega Center', '2024-12-28', 'James Rodriguez', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: December 28, 2024
Inspector: James Rodriguez

OVERALL RATING: EXCELLENT

Model facility - recommended as benchmark. Inventory organization is exemplary.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(6, 'Pacific Northwest Depot', '2024-10-28', 'David Kim', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: October 28, 2024
Inspector: David Kim

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: First aid stations fully stocked. AED units tested and operational.'),
(7, 'Mountain West Facility', '2024-11-15', 'Patricia Evans', 'Critical', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: November 15, 2024
Inspector: Patricia Evans

OVERALL RATING: CRITICAL

URGENT: Multiple life-safety violations requiring immediate remediation.

SAFETY: Forklift daily inspection logs complete and current.

FOLLOW-UP REQUIRED:
- Install additional security cameras.'),
(8, 'Florida Gateway', '2024-10-10', 'David Kim', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: October 10, 2024
Inspector: David Kim

OVERALL RATING: GOOD

Good overall condition. Temperature and humidity within specifications across all zones.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(1, 'West Coast Hub', '2024-11-05', 'James Rodriguez', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: November 05, 2024
Inspector: James Rodriguez

OVERALL RATING: SATISFACTORY

Acceptable conditions with some areas requiring attention within 30 days.

SAFETY: Forklift daily inspection logs complete and current.'),
(2, 'Midwest Distribution', '2024-11-26', 'David Kim', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: November 26, 2024
Inspector: David Kim

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(3, 'East Coast Fulfillment', '2024-11-13', 'Patricia Evans', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: November 13, 2024
Inspector: Patricia Evans

OVERALL RATING: GOOD

Generally well-maintained facility. Minor observations noted for routine follow-up.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.'),
(4, 'Southeast Logistics', '2024-12-22', 'James Rodriguez', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: December 22, 2024
Inspector: James Rodriguez

OVERALL RATING: GOOD

Generally well-maintained facility. Minor observations noted for routine follow-up.

SAFETY: PPE compliance observed at 95% during walkthrough.');

INSERT INTO WAREHOUSE_INSPECTION_NOTES (WAREHOUSE_ID, WAREHOUSE_NAME, INSPECTION_DATE, INSPECTOR, OVERALL_RATING, FOLLOW_UP_REQUIRED, INSPECTION_NOTES) VALUES
(5, 'Texas Mega Center', '2024-10-12', 'Sarah Chen', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: October 12, 2024
Inspector: Sarah Chen

OVERALL RATING: EXCELLENT

Outstanding housekeeping across all zones. All safety systems tested and fully operational.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(6, 'Pacific Northwest Depot', '2024-12-09', 'David Kim', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: December 09, 2024
Inspector: David Kim

OVERALL RATING: EXCELLENT

Outstanding housekeeping across all zones. All safety systems tested and fully operational.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.'),
(7, 'Mountain West Facility', '2024-10-18', 'David Kim', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: October 18, 2024
Inspector: David Kim

OVERALL RATING: SATISFACTORY

Satisfactory overall but housekeeping standards inconsistent between shifts.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(8, 'Florida Gateway', '2024-11-15', 'James Rodriguez', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: November 15, 2024
Inspector: James Rodriguez

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: Emergency lighting tested - all units operational.'),
(1, 'West Coast Hub', '2024-11-18', 'James Rodriguez', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: November 18, 2024
Inspector: James Rodriguez

OVERALL RATING: EXCELLENT

All zones passed inspection with no findings. Aisles clear, racking in excellent condition.

SAFETY: Safety signage visible and up to date in all zones.'),
(2, 'Midwest Distribution', '2024-12-28', 'James Rodriguez', 'Critical', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: December 28, 2024
Inspector: James Rodriguez

OVERALL RATING: CRITICAL

CRITICAL FAILURE: Core infrastructure systems non-functional. Operations at risk.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.

FOLLOW-UP REQUIRED:
- Complete overdue equipment calibration.'),
(3, 'East Coast Fulfillment', '2024-11-16', 'David Kim', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: November 16, 2024
Inspector: David Kim

OVERALL RATING: GOOD

Facility in good condition. Inventory accuracy high and receiving processes efficient.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(4, 'Southeast Logistics', '2024-11-01', 'David Kim', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: November 01, 2024
Inspector: David Kim

OVERALL RATING: GOOD

Good overall condition. Temperature and humidity within specifications across all zones.

SAFETY: First aid stations fully stocked. AED units tested and operational.'),
(5, 'Texas Mega Center', '2024-10-22', 'Maria Santos', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: October 22, 2024
Inspector: Maria Santos

OVERALL RATING: GOOD

Facility in good condition. Inventory accuracy high and receiving processes efficient.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(6, 'Pacific Northwest Depot', '2025-01-11', 'Maria Santos', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: January 11, 2025
Inspector: Maria Santos

OVERALL RATING: GOOD

Good overall condition. Temperature and humidity within specifications across all zones.

SAFETY: First aid stations fully stocked. AED units tested and operational.'),
(7, 'Mountain West Facility', '2024-10-23', 'Maria Santos', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: October 23, 2024
Inspector: Maria Santos

OVERALL RATING: SATISFACTORY

Acceptable conditions with some areas requiring attention within 30 days.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.'),
(8, 'Florida Gateway', '2024-11-27', 'James Rodriguez', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: November 27, 2024
Inspector: James Rodriguez

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(1, 'West Coast Hub', '2024-11-08', 'James Rodriguez', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: November 08, 2024
Inspector: James Rodriguez

OVERALL RATING: GOOD

Good overall condition. Temperature and humidity within specifications across all zones.

SAFETY: Emergency lighting tested - all units operational.'),
(2, 'Midwest Distribution', '2024-11-07', 'David Kim', 'Poor', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: November 07, 2024
Inspector: David Kim

OVERALL RATING: POOR

Serious concerns about facility condition. Temperature control systems inadequate.

SAFETY: Spill kits present and fully stocked at all hazmat locations.

FOLLOW-UP REQUIRED:
- Repair HVAC system in affected zone.
- Repaint fading floor markings.
- Complete overdue equipment calibration.'),
(3, 'East Coast Fulfillment', '2024-12-07', 'James Rodriguez', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: December 07, 2024
Inspector: James Rodriguez

OVERALL RATING: GOOD

Facility in good condition. Inventory accuracy high and receiving processes efficient.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(4, 'Southeast Logistics', '2024-12-22', 'Patricia Evans', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: December 22, 2024
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: First aid stations fully stocked. AED units tested and operational.'),
(5, 'Texas Mega Center', '2025-01-02', 'Patricia Evans', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: January 02, 2025
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Acceptable conditions with some areas requiring attention within 30 days.

SAFETY: Safety signage visible and up to date in all zones.'),
(6, 'Pacific Northwest Depot', '2024-12-10', 'David Kim', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: December 10, 2024
Inspector: David Kim

OVERALL RATING: EXCELLENT

All zones passed inspection with no findings. Aisles clear, racking in excellent condition.

SAFETY: Safety signage visible and up to date in all zones.'),
(7, 'Mountain West Facility', '2024-10-19', 'Patricia Evans', 'Critical', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: October 19, 2024
Inspector: Patricia Evans

OVERALL RATING: CRITICAL

CRITICAL FAILURE: Core infrastructure systems non-functional. Operations at risk.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.

FOLLOW-UP REQUIRED:
- Address humidity control issues.'),
(8, 'Florida Gateway', '2024-10-20', 'Sarah Chen', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: October 20, 2024
Inspector: Sarah Chen

OVERALL RATING: SATISFACTORY

Acceptable conditions with some areas requiring attention within 30 days.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.');

INSERT INTO WAREHOUSE_INSPECTION_NOTES (WAREHOUSE_ID, WAREHOUSE_NAME, INSPECTION_DATE, INSPECTOR, OVERALL_RATING, FOLLOW_UP_REQUIRED, INSPECTION_NOTES) VALUES
(1, 'West Coast Hub', '2024-12-26', 'James Rodriguez', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: December 26, 2024
Inspector: James Rodriguez

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: PPE compliance observed at 95% during walkthrough.

FOLLOW-UP REQUIRED:
- Install additional security cameras.
- Address humidity control issues.'),
(2, 'Midwest Distribution', '2024-11-30', 'Maria Santos', 'Poor', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: November 30, 2024
Inspector: Maria Santos

OVERALL RATING: POOR

Below acceptable standards. Equipment maintenance overdue and safety violations found.

SAFETY: Forklift daily inspection logs complete and current.

FOLLOW-UP REQUIRED:
- Replace failed emergency lighting units.'),
(3, 'East Coast Fulfillment', '2024-10-04', 'Sarah Chen', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: October 04, 2024
Inspector: Sarah Chen

OVERALL RATING: GOOD

Generally well-maintained facility. Minor observations noted for routine follow-up.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(4, 'Southeast Logistics', '2024-11-12', 'Maria Santos', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: November 12, 2024
Inspector: Maria Santos

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: Spill kits present and fully stocked at all hazmat locations.

FOLLOW-UP REQUIRED:
- Replace failed emergency lighting units.
- Schedule pest control follow-up treatment.'),
(5, 'Texas Mega Center', '2024-12-06', 'James Rodriguez', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: December 06, 2024
Inspector: James Rodriguez

OVERALL RATING: EXCELLENT

All zones passed inspection with no findings. Aisles clear, racking in excellent condition.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(6, 'Pacific Northwest Depot', '2024-11-07', 'Maria Santos', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: November 07, 2024
Inspector: Maria Santos

OVERALL RATING: EXCELLENT

Model facility - recommended as benchmark. Inventory organization is exemplary.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(7, 'Mountain West Facility', '2024-10-06', 'Patricia Evans', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: October 06, 2024
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Satisfactory overall but housekeeping standards inconsistent between shifts.

SAFETY: Forklift daily inspection logs complete and current.

FOLLOW-UP REQUIRED:
- Install additional security cameras.
- Schedule pest control follow-up treatment.
- Replace failed emergency lighting units.'),
(8, 'Florida Gateway', '2024-10-10', 'James Rodriguez', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: October 10, 2024
Inspector: James Rodriguez

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(1, 'West Coast Hub', '2024-12-21', 'Patricia Evans', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: December 21, 2024
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Satisfactory overall but housekeeping standards inconsistent between shifts.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(2, 'Midwest Distribution', '2024-11-04', 'James Rodriguez', 'Poor', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: November 04, 2024
Inspector: James Rodriguez

OVERALL RATING: POOR

Below acceptable standards. Equipment maintenance overdue and safety violations found.

SAFETY: Safety signage visible and up to date in all zones.

FOLLOW-UP REQUIRED:
- Schedule pest control follow-up treatment.
- Repair HVAC system in affected zone.
- Enforce maximum pallet stack height limits.'),
(3, 'East Coast Fulfillment', '2024-10-07', 'James Rodriguez', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: October 07, 2024
Inspector: James Rodriguez

OVERALL RATING: GOOD

Generally well-maintained facility. Minor observations noted for routine follow-up.

SAFETY: Forklift daily inspection logs complete and current.'),
(4, 'Southeast Logistics', '2024-12-09', 'Maria Santos', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: December 09, 2024
Inspector: Maria Santos

OVERALL RATING: GOOD

Strong operational controls observed. Staff knowledgeable about emergency procedures.

SAFETY: Forklift daily inspection logs complete and current.'),
(5, 'Texas Mega Center', '2024-12-10', 'James Rodriguez', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: December 10, 2024
Inspector: James Rodriguez

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: Emergency lighting tested - all units operational.

FOLLOW-UP REQUIRED:
- Enforce maximum pallet stack height limits.'),
(6, 'Pacific Northwest Depot', '2024-10-06', 'Patricia Evans', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: October 06, 2024
Inspector: Patricia Evans

OVERALL RATING: GOOD

Facility in good condition. Inventory accuracy high and receiving processes efficient.

SAFETY: Forklift daily inspection logs complete and current.'),
(7, 'Mountain West Facility', '2024-12-30', 'Patricia Evans', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: December 30, 2024
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.'),
(8, 'Florida Gateway', '2024-11-03', 'Patricia Evans', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: November 03, 2024
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Acceptable conditions with some areas requiring attention within 30 days.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(1, 'West Coast Hub', '2024-12-22', 'Patricia Evans', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: December 22, 2024
Inspector: Patricia Evans

OVERALL RATING: GOOD

Generally well-maintained facility. Minor observations noted for routine follow-up.

SAFETY: Forklift daily inspection logs complete and current.'),
(2, 'Midwest Distribution', '2024-11-16', 'David Kim', 'Poor', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: November 16, 2024
Inspector: David Kim

OVERALL RATING: POOR

Serious concerns about facility condition. Temperature control systems inadequate.

SAFETY: Emergency lighting tested - all units operational.

FOLLOW-UP REQUIRED:
- Repair HVAC system in affected zone.'),
(3, 'East Coast Fulfillment', '2024-11-28', 'David Kim', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: November 28, 2024
Inspector: David Kim

OVERALL RATING: GOOD

Facility in good condition. Inventory accuracy high and receiving processes efficient.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(4, 'Southeast Logistics', '2024-11-14', 'Sarah Chen', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: November 14, 2024
Inspector: Sarah Chen

OVERALL RATING: EXCELLENT

Model facility - recommended as benchmark. Inventory organization is exemplary.

SAFETY: Forklift daily inspection logs complete and current.');

INSERT INTO WAREHOUSE_INSPECTION_NOTES (WAREHOUSE_ID, WAREHOUSE_NAME, INSPECTION_DATE, INSPECTOR, OVERALL_RATING, FOLLOW_UP_REQUIRED, INSPECTION_NOTES) VALUES
(5, 'Texas Mega Center', '2025-01-09', 'David Kim', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: January 09, 2025
Inspector: David Kim

OVERALL RATING: EXCELLENT

All zones passed inspection with no findings. Aisles clear, racking in excellent condition.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.'),
(6, 'Pacific Northwest Depot', '2025-01-01', 'Patricia Evans', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: January 01, 2025
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(7, 'Mountain West Facility', '2024-11-30', 'Sarah Chen', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: November 30, 2024
Inspector: Sarah Chen

OVERALL RATING: SATISFACTORY

Acceptable conditions with some areas requiring attention within 30 days.

SAFETY: PPE compliance observed at 95% during walkthrough.

FOLLOW-UP REQUIRED:
- Complete overdue equipment calibration.'),
(8, 'Florida Gateway', '2025-01-07', 'Patricia Evans', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: January 07, 2025
Inspector: Patricia Evans

OVERALL RATING: EXCELLENT

Model facility - recommended as benchmark. Inventory organization is exemplary.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(1, 'West Coast Hub', '2024-12-09', 'James Rodriguez', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: December 09, 2024
Inspector: James Rodriguez

OVERALL RATING: SATISFACTORY

Acceptable conditions with some areas requiring attention within 30 days.

SAFETY: First aid stations fully stocked. AED units tested and operational.

FOLLOW-UP REQUIRED:
- Repaint fading floor markings.'),
(2, 'Midwest Distribution', '2024-10-08', 'Maria Santos', 'Poor', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: October 08, 2024
Inspector: Maria Santos

OVERALL RATING: POOR

Significant deficiencies identified. Mandatory follow-up inspection required.

SAFETY: Emergency lighting tested - all units operational.

FOLLOW-UP REQUIRED:
- Replace deteriorating dock door seal.
- Replace failed emergency lighting units.
- Update emergency procedures documentation.'),
(3, 'East Coast Fulfillment', '2024-12-20', 'Patricia Evans', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: December 20, 2024
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: PPE compliance observed at 95% during walkthrough.

FOLLOW-UP REQUIRED:
- Update emergency procedures documentation.
- Address humidity control issues.'),
(4, 'Southeast Logistics', '2024-10-30', 'Sarah Chen', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: October 30, 2024
Inspector: Sarah Chen

OVERALL RATING: EXCELLENT

All zones passed inspection with no findings. Aisles clear, racking in excellent condition.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(5, 'Texas Mega Center', '2024-10-25', 'Patricia Evans', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: October 25, 2024
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Acceptable conditions with some areas requiring attention within 30 days.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(6, 'Pacific Northwest Depot', '2024-11-20', 'David Kim', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: November 20, 2024
Inspector: David Kim

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: Emergency lighting tested - all units operational.'),
(7, 'Mountain West Facility', '2024-12-22', 'Patricia Evans', 'Poor', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: December 22, 2024
Inspector: Patricia Evans

OVERALL RATING: POOR

Serious concerns about facility condition. Temperature control systems inadequate.

SAFETY: Emergency lighting tested - all units operational.

FOLLOW-UP REQUIRED:
- Replace failed emergency lighting units.
- Complete overdue equipment calibration.
- Install additional security cameras.'),
(8, 'Florida Gateway', '2024-10-15', 'James Rodriguez', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: October 15, 2024
Inspector: James Rodriguez

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: Forklift daily inspection logs complete and current.'),
(1, 'West Coast Hub', '2024-10-02', 'Sarah Chen', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: October 02, 2024
Inspector: Sarah Chen

OVERALL RATING: GOOD

Strong operational controls observed. Staff knowledgeable about emergency procedures.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(2, 'Midwest Distribution', '2024-11-23', 'Sarah Chen', 'Poor', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: November 23, 2024
Inspector: Sarah Chen

OVERALL RATING: POOR

Below acceptable standards. Equipment maintenance overdue and safety violations found.

SAFETY: Emergency lighting tested - all units operational.

FOLLOW-UP REQUIRED:
- Replace deteriorating dock door seal.'),
(3, 'East Coast Fulfillment', '2024-10-07', 'James Rodriguez', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: October 07, 2024
Inspector: James Rodriguez

OVERALL RATING: GOOD

Generally well-maintained facility. Minor observations noted for routine follow-up.

SAFETY: Safety signage visible and up to date in all zones.'),
(4, 'Southeast Logistics', '2024-11-05', 'Sarah Chen', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: November 05, 2024
Inspector: Sarah Chen

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: Forklift daily inspection logs complete and current.

FOLLOW-UP REQUIRED:
- Repaint fading floor markings.
- Replace failed emergency lighting units.
- Repair HVAC system in affected zone.'),
(5, 'Texas Mega Center', '2024-10-27', 'Sarah Chen', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: October 27, 2024
Inspector: Sarah Chen

OVERALL RATING: GOOD

Strong operational controls observed. Staff knowledgeable about emergency procedures.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.'),
(6, 'Pacific Northwest Depot', '2024-12-07', 'David Kim', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: December 07, 2024
Inspector: David Kim

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: First aid stations fully stocked. AED units tested and operational.

FOLLOW-UP REQUIRED:
- Update emergency procedures documentation.
- Replace deteriorating dock door seal.
- Repaint fading floor markings.'),
(7, 'Mountain West Facility', '2024-11-25', 'David Kim', 'Poor', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: November 25, 2024
Inspector: David Kim

OVERALL RATING: POOR

Multiple critical findings requiring immediate corrective action within 14 days.

SAFETY: Safety signage visible and up to date in all zones.

FOLLOW-UP REQUIRED:
- Repaint fading floor markings.
- Replace deteriorating dock door seal.'),
(8, 'Florida Gateway', '2025-01-03', 'Maria Santos', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: January 03, 2025
Inspector: Maria Santos

OVERALL RATING: EXCELLENT

All zones passed inspection with no findings. Aisles clear, racking in excellent condition.

SAFETY: Safety signage visible and up to date in all zones.');

INSERT INTO WAREHOUSE_INSPECTION_NOTES (WAREHOUSE_ID, WAREHOUSE_NAME, INSPECTION_DATE, INSPECTOR, OVERALL_RATING, FOLLOW_UP_REQUIRED, INSPECTION_NOTES) VALUES
(1, 'West Coast Hub', '2024-12-14', 'Patricia Evans', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: December 14, 2024
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(2, 'Midwest Distribution', '2025-01-12', 'David Kim', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: January 12, 2025
Inspector: David Kim

OVERALL RATING: SATISFACTORY

Satisfactory overall but housekeeping standards inconsistent between shifts.

SAFETY: Safety signage visible and up to date in all zones.'),
(3, 'East Coast Fulfillment', '2024-10-18', 'Sarah Chen', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: October 18, 2024
Inspector: Sarah Chen

OVERALL RATING: SATISFACTORY

Satisfactory overall but housekeeping standards inconsistent between shifts.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(4, 'Southeast Logistics', '2024-12-19', 'James Rodriguez', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: December 19, 2024
Inspector: James Rodriguez

OVERALL RATING: GOOD

Generally well-maintained facility. Minor observations noted for routine follow-up.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(5, 'Texas Mega Center', '2024-10-24', 'Sarah Chen', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: October 24, 2024
Inspector: Sarah Chen

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.

FOLLOW-UP REQUIRED:
- Schedule pest control follow-up treatment.
- Update emergency procedures documentation.'),
(6, 'Pacific Northwest Depot', '2024-11-12', 'Sarah Chen', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: November 12, 2024
Inspector: Sarah Chen

OVERALL RATING: GOOD

Generally well-maintained facility. Minor observations noted for routine follow-up.

SAFETY: First aid stations fully stocked. AED units tested and operational.'),
(7, 'Mountain West Facility', '2024-12-23', 'Sarah Chen', 'Poor', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: December 23, 2024
Inspector: Sarah Chen

OVERALL RATING: POOR

Below acceptable standards. Equipment maintenance overdue and safety violations found.

SAFETY: Spill kits present and fully stocked at all hazmat locations.

FOLLOW-UP REQUIRED:
- Address humidity control issues.'),
(8, 'Florida Gateway', '2024-11-02', 'James Rodriguez', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: November 02, 2024
Inspector: James Rodriguez

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: Emergency lighting tested - all units operational.

FOLLOW-UP REQUIRED:
- Replace failed emergency lighting units.'),
(1, 'West Coast Hub', '2024-12-09', 'Maria Santos', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: December 09, 2024
Inspector: Maria Santos

OVERALL RATING: EXCELLENT

All zones passed inspection with no findings. Aisles clear, racking in excellent condition.

SAFETY: Emergency lighting tested - all units operational.'),
(2, 'Midwest Distribution', '2024-10-31', 'Sarah Chen', 'Critical', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: October 31, 2024
Inspector: Sarah Chen

OVERALL RATING: CRITICAL

URGENT: Multiple life-safety violations requiring immediate remediation.

SAFETY: PPE compliance observed at 95% during walkthrough.

FOLLOW-UP REQUIRED:
- Update emergency procedures documentation.
- Install additional security cameras.'),
(3, 'East Coast Fulfillment', '2024-11-18', 'Maria Santos', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: November 18, 2024
Inspector: Maria Santos

OVERALL RATING: SATISFACTORY

Acceptable conditions with some areas requiring attention within 30 days.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(4, 'Southeast Logistics', '2025-01-12', 'Patricia Evans', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: January 12, 2025
Inspector: Patricia Evans

OVERALL RATING: GOOD

Strong operational controls observed. Staff knowledgeable about emergency procedures.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(5, 'Texas Mega Center', '2024-10-22', 'Maria Santos', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: October 22, 2024
Inspector: Maria Santos

OVERALL RATING: EXCELLENT

All zones passed inspection with no findings. Aisles clear, racking in excellent condition.

SAFETY: Emergency lighting tested - all units operational.'),
(6, 'Pacific Northwest Depot', '2025-01-03', 'James Rodriguez', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: January 03, 2025
Inspector: James Rodriguez

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: First aid stations fully stocked. AED units tested and operational.'),
(7, 'Mountain West Facility', '2024-10-27', 'Maria Santos', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: October 27, 2024
Inspector: Maria Santos

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: First aid stations fully stocked. AED units tested and operational.'),
(8, 'Florida Gateway', '2025-01-05', 'Patricia Evans', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: January 05, 2025
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: First aid stations fully stocked. AED units tested and operational.

FOLLOW-UP REQUIRED:
- Replace deteriorating dock door seal.
- Replace failed emergency lighting units.'),
(1, 'West Coast Hub', '2024-11-07', 'David Kim', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: November 07, 2024
Inspector: David Kim

OVERALL RATING: SATISFACTORY

Satisfactory overall but housekeeping standards inconsistent between shifts.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(2, 'Midwest Distribution', '2024-10-24', 'Maria Santos', 'Poor', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: October 24, 2024
Inspector: Maria Santos

OVERALL RATING: POOR

Multiple critical findings requiring immediate corrective action within 14 days.

SAFETY: Emergency lighting tested - all units operational.

FOLLOW-UP REQUIRED:
- Update emergency procedures documentation.
- Address humidity control issues.'),
(3, 'East Coast Fulfillment', '2024-10-12', 'Sarah Chen', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: October 12, 2024
Inspector: Sarah Chen

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: Forklift daily inspection logs complete and current.'),
(4, 'Southeast Logistics', '2025-01-03', 'James Rodriguez', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: January 03, 2025
Inspector: James Rodriguez

OVERALL RATING: GOOD

Generally well-maintained facility. Minor observations noted for routine follow-up.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.');

INSERT INTO WAREHOUSE_INSPECTION_NOTES (WAREHOUSE_ID, WAREHOUSE_NAME, INSPECTION_DATE, INSPECTOR, OVERALL_RATING, FOLLOW_UP_REQUIRED, INSPECTION_NOTES) VALUES
(5, 'Texas Mega Center', '2024-10-02', 'James Rodriguez', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: October 02, 2024
Inspector: James Rodriguez

OVERALL RATING: SATISFACTORY

Satisfactory overall but housekeeping standards inconsistent between shifts.

SAFETY: Spill kits present and fully stocked at all hazmat locations.

FOLLOW-UP REQUIRED:
- Repaint fading floor markings.
- Replace deteriorating dock door seal.
- Enforce maximum pallet stack height limits.'),
(6, 'Pacific Northwest Depot', '2025-01-09', 'David Kim', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: January 09, 2025
Inspector: David Kim

OVERALL RATING: EXCELLENT

All zones passed inspection with no findings. Aisles clear, racking in excellent condition.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.'),
(7, 'Mountain West Facility', '2024-11-01', 'Maria Santos', 'Poor', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: November 01, 2024
Inspector: Maria Santos

OVERALL RATING: POOR

Serious concerns about facility condition. Temperature control systems inadequate.

SAFETY: Safety signage visible and up to date in all zones.

FOLLOW-UP REQUIRED:
- Update emergency procedures documentation.
- Address humidity control issues.
- Schedule pest control follow-up treatment.'),
(8, 'Florida Gateway', '2024-11-05', 'Maria Santos', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: November 05, 2024
Inspector: Maria Santos

OVERALL RATING: EXCELLENT

Outstanding housekeeping across all zones. All safety systems tested and fully operational.

SAFETY: Forklift daily inspection logs complete and current.'),
(1, 'West Coast Hub', '2024-12-12', 'Sarah Chen', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: December 12, 2024
Inspector: Sarah Chen

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: Forklift daily inspection logs complete and current.

FOLLOW-UP REQUIRED:
- Schedule pest control follow-up treatment.'),
(2, 'Midwest Distribution', '2024-10-29', 'Sarah Chen', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: October 29, 2024
Inspector: Sarah Chen

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: Forklift daily inspection logs complete and current.

FOLLOW-UP REQUIRED:
- Repaint fading floor markings.
- Replace failed emergency lighting units.
- Address humidity control issues.'),
(3, 'East Coast Fulfillment', '2024-12-15', 'James Rodriguez', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: December 15, 2024
Inspector: James Rodriguez

OVERALL RATING: SATISFACTORY

Acceptable conditions with some areas requiring attention within 30 days.

SAFETY: Safety signage visible and up to date in all zones.

FOLLOW-UP REQUIRED:
- Update emergency procedures documentation.'),
(4, 'Southeast Logistics', '2025-01-12', 'Maria Santos', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: January 12, 2025
Inspector: Maria Santos

OVERALL RATING: SATISFACTORY

Satisfactory overall but housekeeping standards inconsistent between shifts.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.'),
(5, 'Texas Mega Center', '2024-12-03', 'Patricia Evans', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: December 03, 2024
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: Spill kits present and fully stocked at all hazmat locations.

FOLLOW-UP REQUIRED:
- Enforce maximum pallet stack height limits.
- Replace deteriorating dock door seal.'),
(6, 'Pacific Northwest Depot', '2024-11-25', 'David Kim', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: November 25, 2024
Inspector: David Kim

OVERALL RATING: GOOD

Generally well-maintained facility. Minor observations noted for routine follow-up.

SAFETY: First aid stations fully stocked. AED units tested and operational.'),
(7, 'Mountain West Facility', '2024-10-26', 'David Kim', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: October 26, 2024
Inspector: David Kim

OVERALL RATING: SATISFACTORY

Satisfactory overall but housekeeping standards inconsistent between shifts.

SAFETY: Spill kits present and fully stocked at all hazmat locations.'),
(8, 'Florida Gateway', '2024-11-08', 'Maria Santos', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: November 08, 2024
Inspector: Maria Santos

OVERALL RATING: GOOD

Strong operational controls observed. Staff knowledgeable about emergency procedures.

SAFETY: First aid stations fully stocked. AED units tested and operational.'),
(1, 'West Coast Hub', '2024-10-07', 'James Rodriguez', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: October 07, 2024
Inspector: James Rodriguez

OVERALL RATING: EXCELLENT

Outstanding housekeeping across all zones. All safety systems tested and fully operational.

SAFETY: Forklift daily inspection logs complete and current.'),
(2, 'Midwest Distribution', '2025-01-01', 'Maria Santos', 'Critical', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: January 01, 2025
Inspector: Maria Santos

OVERALL RATING: CRITICAL

CRITICAL FAILURE: Core infrastructure systems non-functional. Operations at risk.

SAFETY: Spill kits present and fully stocked at all hazmat locations.

FOLLOW-UP REQUIRED:
- Install additional security cameras.
- Schedule pest control follow-up treatment.'),
(3, 'East Coast Fulfillment', '2024-11-10', 'Maria Santos', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: November 10, 2024
Inspector: Maria Santos

OVERALL RATING: SATISFACTORY

Satisfactory overall but housekeeping standards inconsistent between shifts.

SAFETY: Forklift daily inspection logs complete and current.

FOLLOW-UP REQUIRED:
- Replace deteriorating dock door seal.
- Complete overdue equipment calibration.'),
(4, 'Southeast Logistics', '2024-10-29', 'David Kim', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: October 29, 2024
Inspector: David Kim

OVERALL RATING: SATISFACTORY

Acceptable conditions with some areas requiring attention within 30 days.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.

FOLLOW-UP REQUIRED:
- Schedule pest control follow-up treatment.'),
(5, 'Texas Mega Center', '2024-11-12', 'Patricia Evans', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: November 12, 2024
Inspector: Patricia Evans

OVERALL RATING: GOOD

Good overall condition. Temperature and humidity within specifications across all zones.

SAFETY: Forklift daily inspection logs complete and current.'),
(6, 'Pacific Northwest Depot', '2024-12-20', 'Maria Santos', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: December 20, 2024
Inspector: Maria Santos

OVERALL RATING: GOOD

Generally well-maintained facility. Minor observations noted for routine follow-up.

SAFETY: Forklift daily inspection logs complete and current.'),
(7, 'Mountain West Facility', '2025-01-13', 'Sarah Chen', 'Critical', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: January 13, 2025
Inspector: Sarah Chen

OVERALL RATING: CRITICAL

CRITICAL: Facility does not meet minimum safety and operational standards.

SAFETY: Emergency lighting tested - all units operational.

FOLLOW-UP REQUIRED:
- Replace failed emergency lighting units.
- Update emergency procedures documentation.
- Repair HVAC system in affected zone.'),
(8, 'Florida Gateway', '2024-12-07', 'James Rodriguez', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: December 07, 2024
Inspector: James Rodriguez

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: Safety signage visible and up to date in all zones.');

INSERT INTO WAREHOUSE_INSPECTION_NOTES (WAREHOUSE_ID, WAREHOUSE_NAME, INSPECTION_DATE, INSPECTOR, OVERALL_RATING, FOLLOW_UP_REQUIRED, INSPECTION_NOTES) VALUES
(1, 'West Coast Hub', '2024-12-15', 'Patricia Evans', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: December 15, 2024
Inspector: Patricia Evans

OVERALL RATING: GOOD

Good overall condition. Temperature and humidity within specifications across all zones.

SAFETY: First aid stations fully stocked. AED units tested and operational.'),
(2, 'Midwest Distribution', '2024-11-26', 'Maria Santos', 'Poor', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: November 26, 2024
Inspector: Maria Santos

OVERALL RATING: POOR

Significant deficiencies identified. Mandatory follow-up inspection required.

SAFETY: PPE compliance observed at 95% during walkthrough.

FOLLOW-UP REQUIRED:
- Replace failed emergency lighting units.'),
(3, 'East Coast Fulfillment', '2024-10-27', 'David Kim', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: East Coast Fulfillment (Warehouse #3)
Date: October 27, 2024
Inspector: David Kim

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.'),
(4, 'Southeast Logistics', '2024-11-03', 'David Kim', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Southeast Logistics (Warehouse #4)
Date: November 03, 2024
Inspector: David Kim

OVERALL RATING: EXCELLENT

Outstanding housekeeping across all zones. All safety systems tested and fully operational.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(5, 'Texas Mega Center', '2024-11-17', 'David Kim', 'Good', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Texas Mega Center (Warehouse #5)
Date: November 17, 2024
Inspector: David Kim

OVERALL RATING: GOOD

Facility in good condition. Inventory accuracy high and receiving processes efficient.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(6, 'Pacific Northwest Depot', '2024-12-16', 'Patricia Evans', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Pacific Northwest Depot (Warehouse #6)
Date: December 16, 2024
Inspector: Patricia Evans

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: First aid stations fully stocked. AED units tested and operational.

FOLLOW-UP REQUIRED:
- Address humidity control issues.
- Repair HVAC system in affected zone.'),
(7, 'Mountain West Facility', '2024-10-07', 'Sarah Chen', 'Satisfactory', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Mountain West Facility (Warehouse #7)
Date: October 07, 2024
Inspector: Sarah Chen

OVERALL RATING: SATISFACTORY

Meets minimum standards. Several minor findings documented for corrective action.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.'),
(8, 'Florida Gateway', '2024-11-06', 'David Kim', 'Excellent', FALSE, 'WAREHOUSE INSPECTION REPORT
Facility: Florida Gateway (Warehouse #8)
Date: November 06, 2024
Inspector: David Kim

OVERALL RATING: EXCELLENT

Outstanding housekeeping across all zones. All safety systems tested and fully operational.

SAFETY: PPE compliance observed at 95% during walkthrough.'),
(1, 'West Coast Hub', '2024-12-25', 'Maria Santos', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: West Coast Hub (Warehouse #1)
Date: December 25, 2024
Inspector: Maria Santos

OVERALL RATING: SATISFACTORY

Generally adequate but aging infrastructure showing wear in some zones.

SAFETY: Fire extinguishers inspected and within date. Emergency exits clear.

FOLLOW-UP REQUIRED:
- Address humidity control issues.'),
(2, 'Midwest Distribution', '2024-11-28', 'David Kim', 'Satisfactory', TRUE, 'WAREHOUSE INSPECTION REPORT
Facility: Midwest Distribution (Warehouse #2)
Date: November 28, 2024
Inspector: David Kim

OVERALL RATING: SATISFACTORY

Satisfactory overall but housekeeping standards inconsistent between shifts.

SAFETY: Emergency lighting tested - all units operational.

FOLLOW-UP REQUIRED:
- Enforce maximum pallet stack height limits.
- Replace failed emergency lighting units.
- Complete overdue equipment calibration.');
