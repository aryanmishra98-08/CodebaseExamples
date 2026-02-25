@echo off
start /B python main.py
echo %! > logs\warehouse.pid
echo Service started.
