#!/bin/bash

#desactivate prompt logs

pf flow serve --source file_classification --port 8002 --host 0.0.0.0 --engine fastapi --skip-open-browser
