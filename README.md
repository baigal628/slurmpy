
### Submitting jobs to slurm via python2/python3.

I usually use `Snakemake` to manage my workflow on HPC. snakemake can internally submit jobs to any scheduler, but sometimes, I do need to run some commands quickly and I do not want to copy paste the `#SBATCH` header each time.
I googled around and found the repo from [Brent Pederson](https://github.com/brentp/slurmpy). Thanks for making this!

I forked the repo and made some small changes by setting up the default time, queue for the Harvard Odyssey HPC cluster. I also changed how the script is named. I prefix the names with the dates so it can be sorted easily by linux command.

Please check the research computing page for specifications of parameters for Odyssey at [here](https://www.rc.fas.harvard.edu/resources/running-jobs/).


#### default parameters

```Python
from slurmpy import Slurm

# default parameter
s = Slurm("jobname")

print(str(s))
#!/bin/bash

#SBATCH -e logs/jobname.%J.err
#SBATCH -o logs/jobname.%J.out
#SBATCH -J jobname

#SBATCH --time=00:02:00
#SBATCH -n 1
#SBATCH -N 1
#SBATCH -p general
#SBATCH --mem=4000

set -eo pipefail -o nounset

__script__
```

#### change time and queue

```python
s = Slurm("job-name", {"time": "04:00:00", "partition": "shared"})
print(str(s))

print(str(s))
#!/bin/bash

#SBATCH -e logs/jobname.%J.err
#SBATCH -o logs/jobname.%J.out
#SBATCH -J jobname

#SBATCH --time=00:02:00
#SBATCH -n 1
#SBATCH -N 1
#SBATCH -p general
#SBATCH --mem=4000

set -eo pipefail -o nounset

__script__

In [8]: s = Slurm("job-name", {"time": "04:00:00", "partition": "shared"})

In [9]: print(str(s))
#!/bin/bash

#SBATCH -e logs/job-name.%J.err
#SBATCH -o logs/job-name.%J.out
#SBATCH -J job-name

#SBATCH --time=04:00:00
#SBATCH --partition=shared
#SBATCH -n 1
#SBATCH -N 1
#SBATCH -p general
#SBATCH --mem=4000

set -eo pipefail -o nounset

__script__
```

This little utility can handle single letter parameter or full name. e.g. you can specify `p` or `partition`, but note that the default is `-p`, and if you specify `partition`, the `-p` is not overwritten (can be improved to check that). to overwrite the default, use `Slurm("job-name", {"time": "04:00:00", "p": "shared"})`. The same for `time` and `mem`. e.g. If you want to overwrite `mem`, do not use `m`. 


### run/submit jobs 

```python
s.run("""
do
lots
of
stuff
""", name_addition="", tries=1, depends_on=[job_id]))

```

The above will submit the job to `sbatch` automatically write the script to `slurm_scripts/`
and automatically write `logs/{name}.err` and `logs/{name}.out`. It will have today's
date in the log and script names.

The script to run() can also contain `$variables` which are filled with the `cmd_kwarg` dict.
E.g. `echo $name` could be filled with `cmd_kwargs={'name': 'sally'}`

A command can be tested (not sent to queue) by setting the `_cmd` to `bash`.
The default is `sbatch` which submits jobs to slurm.


### Dependencies


Each time `slurmpy.Slurm().run()` is called, it returns the job-id of the submitted job. This
can then be sent to a subsequent job:
```
s = Slurmp()
s.run(..., depends_on=[job_id])

```
to indicate that this job should not run until the the job with `job_id` has finished successfully.


### Install

```Shell

git clone https://github.com/crazyhottommy/slurmpy

cd slurmpy

python setup.py install --user

```

### How to use

```bash
mkdir slurmpy_odyssey
cd slurmpy_odyssey
python
from slurmpy import Slurm
...
exit()

# the scripts will be writen in the slurm_scripts folder and the logs in the logs folder.
find . 
./slurm-scripts
./slurm-scripts/2018-10-09-test-tommyfirstjob.sh
./slurm-scripts/2018-10-09-tommysecondjob.sh
./listfiles2.txt
./mylistfiles.txt
./logs
./logs/2018-10-09-tommysecondjob.55721494.err
./logs/2018-10-09-tommysecondjob.55721494.out
./logs/2018-10-09-test-tommyfirstjob.55718062.err
./logs/2018-10-09-test-tommyfirstjob.55718062.out
```
This way, the `logs` and `slurm_scripts` folder will be generated inside the slurmpy_odyssey folder.
