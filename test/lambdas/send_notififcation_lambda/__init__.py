import os
import sys

cwd = os.environ.get('CODEBUILD_SRC_DIR')
if cwd is None:
    cwd = os.getcwd()
cwd += '/lambdas/send_notification_lambda'
sys.path.insert(1, cwd)
