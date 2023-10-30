[default]
host = "0.0.0.0"
port = 8080
log_level = "INFO"
concurrency = 2
ghe_host = ""
cloud = ""

[testing.driver_params]
# here are parameters for the specific cloud driver of apache libcloud library
# below are params for Google Cloud Platform
# https://libcloud.readthedocs.io/en/stable/compute/drivers/gce.html#libcloud.compute.drivers.gce.GCENodeDriver
user_id = "test@test.iam.gserviceaccount.com"
key = "test.json"
project = "test"
datacenter = "europe-west4-a"

[testing.vm_templates."ubuntu-22-04"]
labels = ["ubuntu-22.04-self-hosted"]
image = "runner-ubuntu-22-04-20231028-0555"
size = "e2-standard-2"

[testing.vm_templates."ubuntu-22-04-arm64"]
labels = ["ubuntu-arm64-22.04-self-hosted"]
image = "runner-ubuntu-22-04-arm64-20231027-0910"
size = "t2a-standard-2"

[testing.vm_templates."freebsd-13-2"]
labels = ["freebsd-13.2-self-hosted"]
image = "runner-freebsd-13-2-20231027-0703"
size = "e2-standard-2"

[testing.vm_templates."windows-server-2022"]
labels = ["windows-server-2022-self-hosted"]
image = "runner-windows-server-2022-20231028-0449"
size = "e2-standard-2"
