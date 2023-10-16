from enum import Enum

from pydantic import BaseModel


class StepConclusion(str, Enum):
    failure = "failure"
    skipped = "skipped"
    success = "success"
    cancelled = "cancelled"


class WorkflowJobConlusion(str, Enum):
    success = "success"
    failure = "failure"
    skipped = "skipped"
    cancelled = "cancelled"
    action_required = "action_required"
    neutral = "neutral"
    timed_out = "timed_out"


class WorkflowStatus(str, Enum):
    queued = "queued"
    in_progress = "in_progress"
    completed = "completed"
    waiting = "waiting"


class StepStatus(str, Enum):
    in_progress = "in_progress"
    completed = "completed"
    queued = "queued"


class Step(BaseModel):
    name: str
    status: StepStatus
    conclusion: StepConclusion | None
    number: int
    started_at: str | None
    completed_at: str | None


class WorkflowJob(BaseModel):
    id: int
    run_id: int
    workflow_name: str | None
    head_branch: str | None
    run_url: str
    run_attempt: int
    node_id: str
    head_sha: str
    url: str
    html_url: str
    status: WorkflowStatus
    conclusion: WorkflowJobConlusion | None
    created_at: str
    started_at: str
    completed_at: str | None
    name: str
    steps: list[Step]
    check_run_url: str
    labels: list[str]
    runner_id: int | None
    runner_name: str | None
    runner_group_id: int | None
    runner_group_name: str | None


class Owner(BaseModel):
    login: str
    id: int
    node_id: str
    avatar_url: str
    gravatar_id: str
    url: str
    html_url: str
    followers_url: str
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: str
    organizations_url: str
    repos_url: str
    events_url: str
    received_events_url: str
    type: str
    site_admin: bool


class Repository(BaseModel):
    id: int
    node_id: str
    name: str
    full_name: str
    private: bool
    owner: Owner
    html_url: str
    description: str | None
    fork: bool
    url: str
    forks_url: str
    keys_url: str
    collaborators_url: str
    teams_url: str
    hooks_url: str
    issue_events_url: str
    events_url: str
    assignees_url: str
    branches_url: str
    tags_url: str
    blobs_url: str
    git_tags_url: str
    git_refs_url: str
    trees_url: str
    statuses_url: str
    languages_url: str
    stargazers_url: str
    contributors_url: str
    subscribers_url: str
    subscription_url: str
    commits_url: str
    git_commits_url: str
    comments_url: str
    issue_comment_url: str
    contents_url: str
    compare_url: str
    merges_url: str
    archive_url: str
    downloads_url: str
    issues_url: str
    pulls_url: str
    milestones_url: str
    notifications_url: str
    labels_url: str
    releases_url: str
    deployments_url: str
    created_at: str
    updated_at: str
    pushed_at: str
    git_url: str
    ssh_url: str
    clone_url: str
    svn_url: str
    homepage: str | None
    size: int
    stargazers_count: int
    watchers_count: int
    language: str | None
    has_issues: bool
    has_projects: bool
    has_downloads: bool
    has_wiki: bool
    has_pages: bool
    has_discussions: bool
    forks_count: int
    mirror_url: str | None
    archived: bool
    disabled: bool
    open_issues_count: int
    license: str | None
    allow_forking: bool
    is_template: bool
    web_commit_signoff_required: bool
    topics: list
    visibility: str
    forks: int
    open_issues: int
    watchers: int
    default_branch: str
    anonymous_access_enabled: bool


class Enterprise(BaseModel):
    id: int
    slug: str
    name: str
    node_id: str
    avatar_url: str
    description: str | None
    website_url: str | None
    html_url: str
    created_at: str
    updated_at: str


class Sender(BaseModel):
    login: str
    id: int
    node_id: str
    avatar_url: str
    gravatar_id: str
    url: str
    html_url: str
    followers_url: str
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: str
    organizations_url: str
    repos_url: str
    events_url: str
    received_events_url: str
    type: str
    site_admin: bool


class Action(str, Enum):
    completed = "completed"
    in_progress = "in_progress"
    queued = "queued"
    waiting = "waiting"


class WorkflowJobWebHook(BaseModel):
    action: Action
    workflow_job: WorkflowJob
    repository: Repository
    enterprise: Enterprise
    sender: Sender
