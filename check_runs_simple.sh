#!/bin/bash

echo "Checking active LinkedIn runs..."
curl -s "https://dataroles-production.up.railway.app/api/runs/active" | python3 -m json.tool

echo -e "\n\nChecking active Indeed runs..."
curl -s "https://dataroles-production.up.railway.app/api/indeed/runs/active" | python3 -m json.tool
