# aws-polly-demo
A script that generates a demo voice sample of every English language Amazon Polly voice.

See a working version of this script here.
https://youtu.be/bWwYeQx9AFo

You'll have the best luck with this for English languages if you set the AWS_DEFAULT_REGION to us-east-1. (Not all regions support all languages.
You can do this at the command line in your project like this:
export AWS_ACCESS_KEY_ID={your_key_ID}
export AWS_SECRET_ACCESS_KEY={your_secret_key}
export AWS_DEFAULT_REGION=us-east-1

If more languages are added to Polly, updating the csv with the relevant fields for those languages will allow for a fresh version of the video to be generated.

This hasn't been tested with non-English languages. Let me know if you try it for that.

A more detailed explanation of this script can be found here:
https://medium.com/@edkohler/creating-amazon-polly-voice-samples-with-moviepy-8df140f96670
