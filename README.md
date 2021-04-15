
### Submitting jobs to slurm via python2/python3.

I usually use `Snakemake` to manage my workflow on HPC. snakemake can internally submit jobs to any scheduler, but sometimes, I do need to run some commands quickly and I do not want to copy paste the `#SBATCH` header each time.
I googled around and found the repo from [Brent Pederson](https://github.com/brentp/slurmpy). Thanks for making this!

I forked the repo and made some small changes by setting up the default time, queue for the Harvard Odyssey HPC cluster. I also changed how the script is named. I prefix the names with the dates so it can be sorted easily by linux command.

Please check the research computing page for specifications of parameters for Odyssey at [here](https://www.rc.fas.harvard.edu/resources/running-jobs/).


#### default parameters

```Python
from slurmpy import Slurm

# default parameter
s = Slurm("job-name")

print(str(s))
#!/bin/bash

#SBATCH -e logs/job-name.%J.err
#SBATCH -o logs/job-name.%J.out
#SBATCH -J job-name

#SBATCH -c 10
#SBATCH --mem=8000

set -eo pipefail -o nounset

module load R
module load perl

__script__

```

#### change CPU and memory

```python

s = Slurm("job-name", {"c": "8", "mem": "16G"})

print(str(s))
#!/bin/bash

#SBATCH -e logs/job-name.%J.err
#SBATCH -o logs/job-name.%J.out
#SBATCH -J job-name

#SBATCH -c 8
#SBATCH --mem=16G

set -eo pipefail -o nounset

module load R
module load perl

__script__

```

### run/submit jobs 

```python
cmd = "ls | wc -l > line.txt"
s.run(cmd, name_addition="", tries=1, depends_on=[job_id]))

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
mkdir slurmpy_kraken
cd slurmpy_kraken
python
```

```python

from slurmpy import Slurm

s = Slurm("Pool87_59", {"mem": "8G"})

print(str(s))


#!/bin/bash

#SBATCH -e logs/Pool8759.%J.err
#SBATCH -o logs/Pool8759.%J.out
#SBATCH -J Pool8759

#SBATCH --mem=8G
#SBATCH -c 10

set -eo pipefail -o nounset

module load R
module load perl

__script__


cmd = "scafe.workflow.sc.solo \
--overwrite=yes \
--run_bam_path=~/bam_files/$sample/outs/possorted_genome_bam.bam\
--run_cellbarcode_path=~/bam_files/$sample/outs/filtered_feature_bc_matrix/barcodes.tsv.gz \
--genome=hg38.gencode_v32 \
--run_tag $sample \
--run_outDir=~/output/$sample"


s.run(cmd, cmd_kwargs={'sample': 'Pool87_59'})

##Later:

Slurm('Pool84_10' , {'mem': '8G'}).run(cmd, cmd_kwargs={'sample': 'Pool84_10'})
Slurm('Pool84_11' , {'mem': '8G'}).run(cmd, cmd_kwargs={'sample': 'Pool84_11'})
Slurm('Pool84_12' , {'mem': '8G'}).run(cmd, cmd_kwargs={'sample': 'Pool84_12'})
...

exit()
```

This way, the `logs` and `slurm_scripts` folder will be generated inside the slurmpy_kraken folder.
