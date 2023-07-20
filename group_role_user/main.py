import json
from uuid import uuid4

import pymongo
from bson import ObjectId
from bson.json_util import dumps
from fastapi import FastAPI
from neo4j import GraphDatabase
from pymongo import MongoClient

app = FastAPI()

mongo_client = MongoClient("mongodb://root:password@localhost:27017/?authMechanism=DEFAULT")
neo4j_client = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

# CREATING NEW GROUPS

@app.post("/create-new-group")
async def create_new_group(input: dict):
    db = mongo_client["project"]
    collection = db["groups"]

    result = collection.insert_one(input)

    with neo4j_client.session() as session:
        session.run("CREATE (g:Group {id: $id})", {"id": str(result.inserted_id)})

# UPDATE GROUPS

@app.put("/update-group/{id}")
async def update_groups(id, update: dict):
    db = mongo_client["project"]
    collection = db["groups"]

    collection.update_one({"_id": ObjectId(id)}, {"$set": update})

# DELETE GROUPS

@app.delete("/delete-group/{id}")
async def delete_group(id):
    db = mongo_client["project"]
    collection = db["groups"]

    collection.delete_one({"_id": ObjectId(id)})

    with neo4j_client.session() as session:
        session.run("MATCH (n:Group) WHERE n.id = $id DETACH DELETE n", {"id": id})

# SHOW GROUPS

@app.get("/get-all-groups")
async def get_all_groups():
    db = mongo_client["project"]
    collection = db["groups"]

    result = collection.find()
    return json.loads(dumps(result))

# CREATE NEW ROLES

@app.post("/create-new-role")
async def create_new_role(input: dict):
    db = mongo_client["project"]
    collection = db["roles"]

    result = collection.insert_one(input)

    with neo4j_client.session() as session:
        session.run("CREATE (r:Role {id: $id})", {"id": str(result.inserted_id)})

# UPDATE ROLES need additional fixes

@app.put("/update-roles")
async def update_roles(input: dict):
    db = mongo_client["project"]
    collection = db["roles"]

    collection.update_one({"_id": ObjectId(input["id"])}, {"$set": {"name": input["name"]}})

# DELETE ROLES

@app.delete("/delete-role/{id}")
async def delete_role(id):
    db = mongo_client["project"]
    collection = db["roles"]

    collection.delete_one({"_id": ObjectId(id)})

    with neo4j_client.session() as session:
        session.run("MATCH (r:Role) WHERE r.id = $id DETACH DELETE r",
        {"id": id})

# SHOW ROLES

@app.get("/show-all-roles")
async def show_all_roles():
    db = mongo_client["project"]
    collection = db["roles"]

    result = collection.find()
    return json.loads(dumps(result))

# BIND GROUP TO ROLE

@app.post("/bind-group-to-role")
async def bind_group_to_role(input: dict):
    with neo4j_client.session() as session:
        session.run("""MATCH (g:Group), (r:Role) WHERE g.id = $group_id AND r.id = $role_id
        MERGE (r)-[:OWNS {permissions: [1,2,3,4,5,6,7,8,9,10]}]->(g)""", {"group_id": input["group-id"], "role_id": input["role-id"]})

# UNBIND GROUP FROM ROLE

@app.delete("/unbind-group-from-role")
async def unbind_group_from_role(input: dict):
    with neo4j_client.session() as session:
        session.run("""MATCH (g:Group), (r:Role), (r)-[rel:OWNS]->(g)
                    WHERE g.id = $group_id AND r.id = $role_id DELETE rel""",
                    {"group_id": input["group-id"], "role_id": input["role-id"]})

# CREATE NEW USER

@app.post("/create-new-user")
async def create_new_user(input: dict):
    db = mongo_client["project"]
    collection = db["users"]

    result = collection.insert_one(input)

    with neo4j_client.session() as session:
        session.run("CREATE (u:User {id: $id})", {"id": str(result.inserted_id)})

    with neo4j_client.session() as session:
        session.run("""
                    MATCH (g:Group), (r:Role), (u:User) WHERE g.id = $group_id AND r.id = $role_id AND u.id = $id
                    MERGE (g)-[:OWNS]->(u) MERGE (u)-[:OWNS]->(r)""",
                    {"group_id": input["group-id"], "role_id": input["role-id"], "id": str(result.inserted_id)}
                )

# UPDATE USER
# DELETE USER
# SHOW ALL USERS
