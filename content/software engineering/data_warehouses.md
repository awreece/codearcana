Title: Data warehousing in the modern era
Tags: databases
Date: 2016-07-29

Data Warehousing (DW) and Business Intelligence (BI) are a pair of concepts almost as old as databases. They spring from the need for enterprises to dig into huge amounts of data to identify business trends over time to anticipate future needs. They are inexorably linked concepts; BI refers to the process (questions, tools, visualizations) that sifts through data to derive value and DW refers to the infrastructure (databases, schemas, and extract-transform-load (ETL) systems) needed to enable this process.

The key insight to DW/BI is that the analytical queries used are *very* resource intensive. Traditional BI workloads scan over months or years of historical data, aggregating over terabytes of data. Because of the explosive scale of the Internet of Things, modern BI workloads have to process similar quantities of information when examining much shorter time slices. For example, an oil company might need to monitor millions of sensor data points every hour to be able to predict broken drill bits in real time. In order to support such expensive BI questions, DW technology has to be incredibly sophisticated.

DW gurus have many practices to enable large scale BI. Since integers are easy to store and fast to query, abstract integer identifiers or “surrogate keys” are used to identify data instead of its semantic value. Star schemas are the result of “denormalizing” many interrelated SQL tables into one fact table that references many dimension tables, allowing BI queries that were previously complicated joins of multiple tables to be a single scan of thea large “fact” table. Many columnar data stores are designed for this kind of denormalization and compress common values extremely well. To achieve sub-minute response times on BI queries without interfering with transactional workflows, ETL is used to pre-aggregate the transactional data and move it into a custom, dedicated DW. 

DW is at an in inflection point; as the world moves to the scale of internet of things and real time analytics, traditional DW practices need to adapt to keep up. Traditional ETL run once an hour does not capture the real time changes needed to anticipate the needs of a modern business. 

