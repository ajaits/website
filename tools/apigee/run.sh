#!/bin/bash
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

ENV_FILE=$1

if [[ $ENV_FILE == "" ]]; then
  echo "No env file specified (e.g. prod.env, staging.env)." >&2
  echo "Example usage: ./run.sh prod.env" >&2
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

# Pass all args, except the first one to the python script.
python3 apigee.py "${@:2}"