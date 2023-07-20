#!/bin/bash

now=$(date)
a="$now prodenv-ampapp"
a=${a// /}
aws rds create-db-cluster-snapshot --db-cluster-identifier ampapp-prodenv-addonsstack-t9yq-ampdbdbcluster-fw71gmspa1pf --db-cluster-snapshot-identifier ${a//:/}