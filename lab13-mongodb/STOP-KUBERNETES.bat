@echo off
kubectl --context docker-desktop -n lab13-mongodb scale statefulset mongo --replicas=0
pause
