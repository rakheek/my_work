#!/home/apps/perl_org/perl-5_12_3/bin/perl
eval 'set -x;
perl=/home/apps/perl_org/perl-5_12_3/bin/perl
Steps2Debug="$[/javascript (myJob.Steps2Debug)]"
pswitch="$[/javascript (myJob.PerlSwitch)]"
api_path=$api_path
if [ -n "$api_path" ] ; then
   pswitch="$pswitch $api_path"
fi
export RemoteDebugAddress=$[/javascript (myJob.RemoteDebugAddress)]
if [ "$Steps2Debug" = "EVAL" -a "$RemoteDebugAddress" != "" ] ; then
  PERLDB_OPTS="RemotePort=$RemoteDebugAddress"
  export PERLDB_OPTS
  PERL5LIB="$[/javascript getProperty ("/projects[$[/myJob/projectName]]/PerlDebLib")]"
  export PERL5LIB 
  pdeb="-d"
  echo "Running perl in debug mode"
fi 
pdeb="$pdeb "

exec $perl $pdeb $pswitch -S $0 ${1+"$@"}'
  if 0;

use strict;
use Ecloud::Ec;
use XML::XPath;

# This is a nuisance
$ENV{PERL_LWP_SSL_VERIFY_HOSTNAME} = 0;
delete $ENV{COMMANDER_HTTP_PROXY};

$SIG{__WARN__} = sub {
  if ($_[0] !~ m!^Use of uninitialized value in string eq at .*?Moose/Meta/Attribute.pm line 1035, <IN> line 249|1035.!)
  {
    print STDERR $_[0];
  }
};

my $has_commander = $ENV{COMMANDER_SERVER};

my $ec = Ecloud::Ec->new_with_options;

die $ec->err if $ec->err;

my $comb_index;
my $jobstep_id;
if ($has_commander)
{
  $comb_index = '$[/myJobStep/combinationIndex]';
  $jobstep_id = '$[/myJobStep/jobStepId]';

  print "$0: --host $ENV{COMMANDER_SERVER} $jobstep_id\n";
} else
{
  $jobstep_id = shift @{$ec->extra_argv} || die "Need job step id";
}

my $jobstep = $ec->Get("/jobSteps[$jobstep_id]") || die $ec->err;

if (!$has_commander)
{
  $comb_index = $jobstep->Get('/properties[combinationIndex]')->value;
}
my $jobid = $jobstep->jobId;

my $job = $ec->Get("/jobs[$jobid]") || die $ec->err;

# Examine prerequisites
my $prereqs = $jobstep->Get('/properties[prerequisites]')->value;
my $cl_sets = $jobstep->Get("/properties[clSets]")->value; # Needed to keep order
my $cl_order = $jobstep->Get("/properties[clOrder]")->value;

my %cl_order;

foreach my $c (split(' ', $cl_order))
{
  my ($cl, $ind) = split('=', $c);
  $cl_order{$cl} = $ind;
}

# Index cl sets by the sum of components
my %cl_sets;
foreach my $set (split(':', $cl_sets))
{
  foreach my $cl (split('-', $set))
  {
    $cl_sets{$set} += $cl_order{$cl};
  }
}

my $cl_num = scalar(keys %cl_sets);

# Find and mark successfull CLs
my %good;
my $bad_cnt;

my $batch = $ec->commander->newBatch('parallel');
$ec->commander->abortOnError(1); # Catch errors
my %r_ids;
my @prereqs = split(' ', $prereqs);

printf "Will examine %d prerequisites\n", scalar(@prereqs);
# Get job step IDs
foreach my $prereq (@prereqs)
{
  my $args = $has_commander ? '/myJob' : "/jobs[$jobid]";
  $r_ids{$prereq} = $batch->getProperty($args . "/preconditions/$prereq");
}

$batch->submit;

my %outcomes;

# get outcomes
# Faster?
my $xml = $batch->{response}->{_xml};

my $xp = XML::XPath->new(xml => $xml);
my @ors;
foreach my $data ($xp->findnodes('//property'))
{
#  my $stepname = ($xp->findnodes('propertyName', $data))[0]->string_value;
  
  my $step_id = ($xp->findnodes('value', $data))[0]->string_value;

  push(@ors, {propertyName => jobStepId => operator => equals => operand1 => $step_id});
}

# 
my $commander = $ec->commander;
my $xPath = $commander->findObjects('jobStep',
                                           {filter => {
                                                       operator => 'and', 
                                                       filter => [
                                                                  # Step names
                                                                  {
                                                                   operator => 'or',
                                                                   filter => \@ors
                                                                  },
                                                                  {
                                                                   operator => 'equals',
                                                                   propertyName => 'outcome',
                                                                   operand1 => 'error',
                                                                  }
                                                                 ],
                                                      }
                                           }
                                          );

# Find failed object IDs
my $nodeset = $xPath->find('//response/objectId');
my $batch1 = $ec->commander->newBatch('parallel');

my @cls_ids;
my $l = length('jobStep-');
my @list = $nodeset->get_nodelist;
printf "Found %d failed steps in combination $comb_index\n", scalar(@list);

foreach my $node (@list)
{
  my $step_id = $node->string_value();
  substr($step_id,0,$l) = '';
  $batch1->getProperty("/jobSteps[$step_id]/clSets")
}

$batch1->submit;

$xml = $batch1->{response}->{_xml};

$xp = XML::XPath->new(xml => $xml);

foreach my $data ($xp->findnodes('//property'))
{
  my $cl_set = ($xp->findnodes('value', $data))[0]->string_value;

  if (exists $good{$cl_set} && !$good{$cl_set})
  {
    # Already marked bad
    next;
  }
  $good{$cl_set} //= 1;     # Set success bu default

  print "marking $cl_set BAD\n";
  $good{$cl_set} = 0;
  $bad_cnt++;
  # Do not bother further if all are bad
  if ($bad_cnt == $cl_num)
  {
    last;
  }
}

# Send email to owners of gad cls

# Find first successfull cl set
if ($bad_cnt != $cl_num) {
  my ($good) = sort {$cl_sets{$a} <=> $cl_sets{$b}} grep { $good{$_}} keys %good;
  $good =~ s/-/ /g;

  print "Found good cls $good\n";

  # Send it to the last step
  if ($has_commander)
  {
    $commander->createProperty('/myJob/goodCls', {value => $good});
  }
} else
{
  # Schedule the next level
  ++$comb_index;
  print "No good cls found, next combination to run: $comb_index\n";
  if ($has_commander)
  {
    $commander->createProperty("/myJob/runCombinations_$comb_index"  , {value => 1});
  }
}
