[default]
ghe_host = ""
cloud = ""

[default.labels]
ubuntu = [""]
ubuntu-arm64 = [""]
freebsd = [""]
windows = [""]

[default.gce.driver_params]
# here are parameters for the specific cloud driver of apache libcloud library
# below are params for Google Cloud Platform
# https://libcloud.readthedocs.io/en/stable/compute/drivers/gce.html#libcloud.compute.drivers.gce.GCENodeDriver
user_id = ""
key = ""
project = ""
datacenter = ""

[default.gce.vm_templates.ubuntu]
image = ""
size = ""

[default.gce.vm_templates."ubuntu-arm64"]
image = ""
size = ""

[default.gce.vm_templates.freebsd]
image = ""
size = ""

[default.gce.vm_templates.windows]
image = ""
size = ""

[testing]
ghe_host = "example.com"
personal_access_token = "github_pat_test"
cloud = "gce"

[testing.gce.driver_params]
user_id = "test@test.iam.gserviceaccount.com"
key = "test.json"
project = "test"
datacenter = "europe-west4-a"
