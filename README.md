# Swiss Hiking Data Updater

Backend service for Swiss Hiking project. This is meant to fetch hiking
routes from online providers and aggregate the result into a Datastore.

## Installation

To install the package and run `bin/runner.py`, run:

```
cd SwissHikingData
pip3 install -e .
```

## How to deploy to GCP Cloud Functions

This project is currently running on GCP, this section records necessary steps
to make it happen (to abide by GCP's requirement). We are going to talk about
Cloud Datastore, Cloud Source Repositories, Cloud Functions, Cloud Build,
Cloud Pub/Sub and Cloud Scheduler.

### Cloud Datastore

Datastore keeps track coordinates as well as update status for each content
provider. Depending on the source, the updater can choose different updating
strategy in order to minimize the load on both side.

To run the project locally with `bin/runner.py`, we need add credential to
our job. You need to first create a Service account for your project and
a json file containing your credentials. Then you can add the path to this
json file to the `GOOGLE_APPLICATION_CREDENTIALS` environment variable.
Details are at https://cloud.google.com/docs/authentication/production.

Accessing Datastore from other APIs within the same project doesn't need
extra configuration.

### Cloud Source Repositories

This project is hosted on Cloud Source Repositories at
https://source.developers.google.com/projects/swiss-hiking/repos/SwissHikingData.
If you are using Github, you need to first import your repository into this
one so other cloud product can use it.

### Cloud Functions

Cloud Functions is a request handler. The request can be HTTP, Pub/Sub, etc.,
they need to be handled by different piece of
code living in `main.py`. This function can live anywhere as long as you have
all dependencies listed in `requirements.txt` alongside this file. In addition,
you can't install any dependencies by yourself, so it's better to use relative
import in the code. This project has a `setup.py`, but this is not required.

The entry point `main.py` is pretty simple, it parse the input data (json)
and acts accordingly. HTTP trigger supports argument list, but it's
recommended to use json data as in this project.

Once you have this file, you can create a Cloud Function using either console
or command line tool.

### Cloud Build

Once you have the project, you may want to use continous integration. Cloud
Build allows you to specify a list of actions to be taken in order to deploy
your function (so the last action should be the deployment itself). To enable
Cloud Build, you need to follow these steps:

1. Create `cloudbuild.yaml` file under the root directory
2. Add a build trigger (on Cloud Build console for example)
3. Add Cloud Functions Developer role to the Cloud Build
   service account (PROJECT_NUMBER@cloudbuild.gserviceaccount.com).
   Go to Console > IAM & Admin > IAM.
4. Let Cloud Functions Service Agent be a Service Account User of the current
   project, i.e. add Cloud Functions Service Agent as a member of App Engine
   default service account with Service Account User role. This can be done
   on Console > IAM & Admin > Service Accounts or by running the following
   command:
   
```
gcloud iam service-accounts add-iam-policy-binding [PROJECT_ID]@appspot.gserviceaccount.com --member=service-[SOME_NUMBER]@gcf-admin-robot.iam.gserviceaccount.com --role=roles/iam.serviceAccountUser`
```

### Cloud Pub/Sub

Pub/Sub lets you publish messages on a topic and subscribe to that topic.
It can be used as a trigger for Cloud Functions. For this project, we
created a topic `data-updater` under the same project. We use `attributes`
field of the message to control the behavior of our function. This is
almost the same as passing a json data to the HTTP request. However,
the testing UI of Cloud Functions doesn't seem to work. We need to
publish a real message on Pub/Sub and look at the log of the execution.

### Cloud Scheduler

One last piece of the puzzle is to schedule the Cloud Function with a
cron job. This cron job publishes regularly to the Pub/Sub topic, thus
invokes the function at the same time.

Cloud Scheduler is currently not available in every region, a walk-around
is to create Cron job in the Frontend App Engine and let the frontend
publish to the Pub/Sub topic.

The frontend code is at https://github.com/lyx-x/SwissHiking.
