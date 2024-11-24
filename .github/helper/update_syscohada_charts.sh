#!/bin/bash
set -e
cd ~ || exit

echo "Setting Up Bench..."

pip install frappe-bench
bench -v init frappe-bench --skip-assets --skip-redis-config-generation --python "$(which python)"
cd ./frappe-bench || exit

echo "Get ERPNext..."
bench get-app --skip-assets erpnext "${GITHUB_WORKSPACE}"

echo "Generating chart of accounts files for Syscohada countries..."
python3 ./apps/erpnext/erpnext/accounts/doctype/account/chart_of_accounts/verified/syscohada_chart_of_accounts.py

cd ./apps/erpnext || exit

echo "Configuring git user..."
git config user.email "developers@erpnext.com"
git config user.name "frappe-pr-bot"

echo "Setting the correct git remote..."
# Here, the git remote is a local file path by default. Let's change it to the upstream repo.
git remote set-url upstream https://github.com/frappe/erpnext.git

echo "Creating a new branch..."
isodate=$(date -u +"%Y-%m-%d")
branch_name="update_syscohada_charts_${BASE_BRANCH}_${isodate}"
git checkout -b "${branch_name}"

echo "Commiting changes..."
git add erpnext/accounts/doctype/account/chart_of_accounts/verified
git commit -m "chore: update syscohada chart of accounts for all countries" -m "no-docs"

gh auth setup-git
git push -u upstream "${branch_name}"

echo "Creating a PR..."
gh pr create --fill --base "${BASE_BRANCH}" --head "${branch_name}" --reviewer ${PR_REVIEWER} -R frappe/erpnext