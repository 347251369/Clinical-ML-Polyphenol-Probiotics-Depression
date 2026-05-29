# FDA Chemical Database Configuration

## Overview

The FDA screening step relies on a Neo4j graph database containing chemical substances and their FDA approval status.

The database dump is located at: `datasets/neo4j.dump`

## Prerequisites

- Neo4j 2025.x (Community or Enterprise)
- Java 21

## Restore the Database

### 1. Install Neo4j

Download and install Neo4j Desktop from https://neo4j.com/download/

### 2. Create a new database

- Open Neo4j Desktop → New → Create project
- Add a Local DBMS (choose version 2025.x)
- Set the password to: `12345678`
- **Do NOT start the database yet**

### 3. Restore the dump

```bash
# Locate your neo4j-admin binary, typically at:
# <Neo4j-Desktop-Project>/dbms-xxxxxx/bin/neo4j-admin.bat (Windows)
# <Neo4j-Desktop-Project>/dbms-xxxxxx/bin/neo4j-admin     (Mac/Linux)

neo4j-admin database load neo4j \
  --from-path=datasets/neo4j.dump \
  --overwrite-destination=true
```

Or in Neo4j Desktop, you can restore via the GUI:
- Select your DBMS → Terminal → run the above command

### 4. Start the database

- Start the DBMS in Neo4j Desktop
- Verify it's running on `bolt://localhost:7687`

## Verify the Restore

Run in Neo4j Browser or cypher-shell:

```cypher
MATCH (c:Chemical) RETURN count(c) as Total_Chemicals;
```

You should see the chemical records loaded.

## Connection Configuration

The application connects to Neo4j with these default credentials (defined in `function.py`):

```python
Neo4jFDA(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="12345678"
)
```

To change the connection, modify the `Neo4jFDA` instantiation in `brain.py` and `function.py`.

## Export (for maintainers)

To re-export the database after changes:

```bash
neo4j-admin database dump neo4j --to-path=datasets/
```

This will overwrite `datasets/neo4j.dump`.
