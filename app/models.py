from enum import Enum

from libcloud.compute.base import NodeImage
from pydantic import BaseModel


class StepConclusion(str, Enum):
    cancelled = "cancelled"
    failure = "failure"
    skipped = "skipped"
    success = "success"


class WorkflowJobConlusion(str, Enum):
    action_required = "action_required"
    cancelled = "cancelled"
    failure = "failure"
    neutral = "neutral"
    skipped = "skipped"
    success = "success"
    timed_out = "timed_out"


class WorkflowStatus(str, Enum):
    completed = "completed"
    in_progress = "in_progress"
    queued = "queued"
    waiting = "waiting"


class StepStatus(str, Enum):
    completed = "completed"
    in_progress = "in_progress"
    queued = "queued"


class Step(BaseModel):
    completed_at: str | None
    conclusion: StepConclusion | None
    name: str
    number: int
    started_at: str | None
    status: StepStatus


class WorkflowJob(BaseModel):
    id: int
    check_run_url: str
    completed_at: str | None
    conclusion: WorkflowJobConlusion | None
    created_at: str
    head_branch: str | None
    head_sha: str
    html_url: str
    labels: list[str]
    name: str
    node_id: str
    run_attempt: int
    run_id: int
    run_url: str
    runner_group_id: int | None
    runner_group_name: str | None
    runner_id: int | None
    runner_name: str | None
    started_at: str
    status: WorkflowStatus
    steps: list[Step]
    url: str
    workflow_name: str | None


class Owner(BaseModel):
    id: int
    avatar_url: str
    events_url: str
    followers_url: str
    following_url: str
    gists_url: str
    gravatar_id: str
    html_url: str
    login: str
    node_id: str
    organizations_url: str
    received_events_url: str
    repos_url: str
    site_admin: bool
    starred_url: str
    subscriptions_url: str
    type: str
    url: str


class License(BaseModel):
    key: str
    name: str
    node_id: str
    spdx_id: str
    url: str | None


class Repository(BaseModel):
    id: int
    allow_forking: bool
    anonymous_access_enabled: bool
    archive_url: str
    archived: bool
    assignees_url: str
    blobs_url: str
    branches_url: str
    clone_url: str
    collaborators_url: str
    comments_url: str
    commits_url: str
    compare_url: str
    contents_url: str
    contributors_url: str
    created_at: str
    default_branch: str
    deployments_url: str
    description: str | None
    disabled: bool
    downloads_url: str
    events_url: str
    fork: bool
    forks_count: int
    forks_url: str
    forks: int
    full_name: str
    git_commits_url: str
    git_refs_url: str
    git_tags_url: str
    git_url: str
    has_discussions: bool
    has_downloads: bool
    has_issues: bool
    has_pages: bool
    has_projects: bool
    has_wiki: bool
    homepage: str | None
    hooks_url: str
    html_url: str
    is_template: bool
    issue_comment_url: str
    issue_events_url: str
    issues_url: str
    keys_url: str
    labels_url: str
    language: str | None
    languages_url: str
    license: License | None
    merges_url: str
    milestones_url: str
    mirror_url: str | None
    name: str
    node_id: str
    notifications_url: str
    open_issues_count: int
    open_issues: int
    owner: Owner
    private: bool
    pulls_url: str
    pushed_at: str
    releases_url: str
    size: int
    ssh_url: str
    stargazers_count: int
    stargazers_url: str
    statuses_url: str
    subscribers_url: str
    subscription_url: str
    svn_url: str
    tags_url: str
    teams_url: str
    topics: list
    trees_url: str
    updated_at: str
    url: str
    visibility: str
    watchers_count: int
    watchers: int
    web_commit_signoff_required: bool


class Enterprise(BaseModel):
    id: int
    avatar_url: str
    created_at: str
    description: str | None
    html_url: str
    name: str
    node_id: str
    slug: str
    updated_at: str
    website_url: str | None


class Sender(BaseModel):
    id: int
    avatar_url: str
    events_url: str
    followers_url: str
    following_url: str
    gists_url: str
    gravatar_id: str
    html_url: str
    login: str
    node_id: str
    organizations_url: str
    received_events_url: str
    repos_url: str
    site_admin: bool
    starred_url: str
    subscriptions_url: str
    type: str
    url: str


class Action(str, Enum):
    completed = "completed"
    in_progress = "in_progress"
    queued = "queued"
    waiting = "waiting"


class WorkflowJobWebHook(BaseModel):
    action: Action
    enterprise: Enterprise
    repository: Repository
    sender: Sender
    workflow_job: WorkflowJob

    @property
    def job_url(self) -> str:
        return self.workflow_job.url

    @property
    def run_id(self) -> int:
        return self.workflow_job.run_id

    @property
    def job_name(self) -> str:
        return self.workflow_job.name

    @property
    def workflow_name(self) -> str:
        return self.workflow_job.workflow_name or ""

    @property
    def runner_name(self) -> str:
        return self.workflow_job.runner_name or ""


class VmTemplate(BaseModel, arbitrary_types_allowed=True):  # type: ignore
    image: NodeImage
    size: str
    labels: list[str]
