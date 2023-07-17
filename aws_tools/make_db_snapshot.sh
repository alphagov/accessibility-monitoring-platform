now=$(date)
a="$now prod-env-amp-app2"
a=${a// /}
aws rds create-db-cluster-snapshot --db-cluster-identifier amp-app-2-prod-env-addonsstack-t9yq-ampdbdbcluster-fw71gmspa1pf --db-cluster-snapshot-identifier ${a//:/}