#!/usr/bin/env bash
# Fetch a JIRA issue as JSON. Usage: ./fetch_jira.sh VOC-1234
# Needs env: JIRA_BASE_URL (e.g. https://yourco.atlassian.net), JIRA_EMAIL, JIRA_TOKEN
# ponytail: curl + jq, no SDK. Add pagination/attachments only if a ticket needs it.
set -euo pipefail

KEY="${1:?usage: fetch_jira.sh <ISSUE-KEY>}"
: "${JIRA_BASE_URL:?set JIRA_BASE_URL}"
: "${JIRA_EMAIL:?set JIRA_EMAIL}"
: "${JIRA_TOKEN:?set JIRA_TOKEN}"

curl -sS -u "${JIRA_EMAIL}:${JIRA_TOKEN}" \
  -H "Accept: application/json" \
  "${JIRA_BASE_URL}/rest/api/3/issue/${KEY}?fields=summary,description,issuetype,priority,components,labels,fixVersions,issuelinks,attachment" \
| jq '{
    key: .key,
    summary: .fields.summary,
    type: .fields.issuetype.name,
    priority: .fields.priority.name,
    components: [.fields.components[]?.name],
    labels: .fields.labels,
    fixVersions: [.fields.fixVersions[]?.name],
    description: .fields.description,
    links: [.fields.issuelinks[]? | {type: .type.name, key: (.outwardIssue.key // .inwardIssue.key)}],
    attachments: [.fields.attachment[]? | .filename]
  }'
