#!/bin/bash

rye build --wheel --clean
docker build . --tag ghcr.io/mohsennz/muon-chatbot-client:latest
