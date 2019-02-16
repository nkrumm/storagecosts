
## Installation


Note: Please see dokku-stack documentation for obtaining SSH credentials

On Dokku instance:
```bash
dokku apps:create storagecosts
```
Next, on your local machine (in folder of this repository)

```bash
git remote add dokku-stack-prod dokku@dokku-stack-prod:storagecosts
git push dokku-stack-prod
```

Finally, back on dokku host:
```
dokku domains:add dokku-stack-prod.labmed.uw.edu
```