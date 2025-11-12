
## Steps to run
```
> docker build -t dz-customers-clustering .
> docker run --name dz-api -p 8000:8000 dz-customers-clustering

```
## Altenatively you can also use below commands to run it in daemon mode.
```

> docker build -t dz-customers-clustering:latest .
> docker run -d \
  --name dz-api \
  -p 8000:8000 \
  dz-customers-clustering:latest
```
