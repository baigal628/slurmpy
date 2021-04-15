r"""
# send in job name and kwargs for slurm params:
>>> s = Slurm("Pool87_59", {"mem": "8G"})
>>> print(str(s))
#!/bin/bash
<BLANKLINE>
#SBATCH -e logs/job-name.%J.err
#SBATCH -o logs/job-name.%J.out
#SBATCH -J job-name
<BLANKLINE>
#SBATCH --mem=8000
#SBATCH -c 16
<BLANKLINE>

set -eo pipefail -o nounset

module load R
module load perl
<BLANKLINE>
__script__

>>> cmd = "scafe.workflow.sc.solo \
--overwrite=yes \
--run_bam_path=/liulab/galib/cHL/SCAFE/SCAFE/analysis/bam_files/$sample/outs/possorted_genome_bam.bam\
--run_cellbarcode_path=/liulab/galib/cHL/SCAFE/SCAFE/analysis/bam_files/$sample/outs/filtered_feature_bc_matrix/barcodes.tsv.gz \
--genome=hg38.gencode_v32 \
--run_tag $sample \
--run_outDir=/liulab/galib/cHL/SCAFE/SCAFE/analysis/output/$sample"


>>> s.run(cmd, cmd_kwargs={'sample': 'Pool87_59'})

"""
from __future__ import print_function

import sys
import os
import subprocess
import tempfile
import atexit
import hashlib
import datetime

TMPL = """\
#!/bin/bash

#SBATCH -e logs/{name}.%J.err
#SBATCH -o logs/{name}.%J.out
#SBATCH -J {name}

{header}

set -eo pipefail -o nounset

module load R
module load perl

__script__

"""


def tmp(suffix=".sh"):
    t = tempfile.mktemp(suffix=suffix)
    atexit.register(os.unlink, t)
    return t

# read https://www.rc.fas.harvard.edu/resources/running-jobs/ for each parameters
class Slurm(object):
    def __init__(self, name, slurm_kwargs=None, tmpl=None, date_in_name=True, scripts_dir="slurm-scripts/"):
        if slurm_kwargs is None:
            slurm_kwargs = {}
        if tmpl is None:
            tmpl = TMPL
        header = []
        # set up some default
        if 'c' not in slurm_kwargs.keys():
            slurm_kwargs['c'] = "10"
        if 'mem' not in slurm_kwargs.keys():
            # in MB, each core is 4G mem
            slurm_kwargs['mem'] = '8000'

        for k, v in slurm_kwargs.items():
            if len(k) > 1:
                k = "--" + k + "="
            else:
                k = "-" + k + " "
            header.append("#SBATCH %s%s" % (k, v))
        self.header = "\n".join(header)
        self.name = "".join(x for x in name.replace(" ", "-") if x.isalnum() or x == "-")
        self.tmpl = tmpl
        self.slurm_kwargs = slurm_kwargs
        if scripts_dir is not None:
            self.scripts_dir = os.path.abspath(scripts_dir)
        else:
            self.scripts_dir = None
        self.date_in_name = bool(date_in_name)

    def __str__(self):
        return self.tmpl.format(name=self.name, header=self.header)

    def _tmpfile(self):
        if self.scripts_dir is None:
            return tmp()
        else:
            if not os.path.exists(self.scripts_dir):
                os.makedirs(self.scripts_dir)
            return "%s/%s.sh" % (self.scripts_dir, self.name)

    def run(self, command, name_addition=None, cmd_kwargs=None, _cmd="sbatch", tries=1, depends_on=None):
        """
        command: a bash command that you want to run
        name_addition: if not specified, the sha1 of the command to run
                       appended to job name, the yyyy-mm-dd
                       date will be added to the job name if self.date_in_name is TRUE (default)
        cmd_kwargs: dict of extra arguments to fill in command
                   (so command itself can be a template).
        _cmd: submit command (change to "bash" for testing).
        tries: try to run a job either this many times or until the first
               success.
        depends_on: job ids that this depends on before it is run (users 'afterok')
        """

        ## put the date first for easy sorting
        if self.date_in_name:
            if name_addition is None:
                name_addition = str(datetime.date.today()) + "-"
            else:
                name_addition = str(datetime.date.today()) + "-" + name_addition
        else:
            if name_addition is None:
                name_addition = hashlib.sha1(command.encode("utf-8")).hexdigest()

        if cmd_kwargs is None:
            cmd_kwargs = {}

        n = self.name
        self.name = self.name.strip(" -")
        # put the date before the jobname
        self.name = name_addition.strip(" -") + "-" + self.name
        args = []
        for k, v in cmd_kwargs.items():
            args.append("export %s=%s" % (k, v))
        args = "\n".join(args)

        tmpl = str(self).replace("__script__", args + "\n###\n" + command)
        if depends_on is None or (len(depends_on) == 1 and depends_on[0] is None):
            depends_on = []

        if "logs/" in tmpl and not os.path.exists("logs/"):
            os.makedirs("logs")

        with open(self._tmpfile(), "w") as sh:
            sh.write(tmpl)

        job_id = None
        for itry in range(1, tries + 1):
            args = [_cmd]
            args.extend([("--dependency=afterok:%d" % int(d)) for d in depends_on])
            if itry > 1:
                mid = "--dependency=afternotok:%d" % job_id
                args.append(mid)
            args.append(sh.name)
            res = subprocess.check_output(args).strip()
            print(res, file=sys.stderr)
            self.name = n
            if not res.startswith(b"Submitted batch"):
                return None
            j_id = int(res.split()[-1])
            if itry == 1:
                job_id = j_id
        return job_id

if __name__ == "__main__":
    import doctest
    doctest.testmod()
