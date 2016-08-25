#!/home/apps/perl_org/perl-5_12_3/bin/perl
# This needed for debugging
eval 'set -x;
     perl=/home/apps/perl_org/perl-5_12_3/bin/perl
export Steps2Debug="$[/javascript (myJob.Steps2Debug)]"
pswitch="$[/javascript (myJob.PerlSwitch)]"
api_path=$api_path
if [ -n "$api_path" ] ; then
   pswitch="$pswitch $api_path"
fi
export RemoteDebugAddress=$[/javascript (myJob.RemoteDebugAddress)]
if [ "$Steps2Debug" != "" -a "$RemoteDebugAddress" != "" ] ; then
  step_name="$[/myJobStep/stepName]"
  for step in $Steps2Debug ;  do
     if [ "$step_name" = "$step" ] ; then
       PERLDB_OPTS="RemotePort=$RemoteDebugAddress"
         export PERLDB_OPTS
       PERL5LIB="$[/javascript getProperty ("/projects[$[/myJob/projectName]]/PerlDebLib")]"
         export PERL5LIB 
       pdeb="-d"
         echo "Running perl in debug mode"
       break 
  fi 
done
fi 
pdeb="$pdeb "

exec $perl $pdeb $pswitch -S $0 ${1+"$@"}'
  if 0;


# Translates .ini into make
use strict;
use Getopt::Long::Descriptive;
use Algorithm::Loops qw/NestedLoops/;
use Graph;
use FindBin qw/$RealBin/;
use Storable qw/store_fd/;
use Sys::Hostname;
use Ecloud::Ec;
use Algorithm::Combinatorics qw/combinations/;

use constant {
  MAX_NUM_TARGETS => 4,
  MAX_NUM_COMB_TARGETS => 3,
};

# This is a nuisance
$ENV{PERL_LWP_SSL_VERIFY_HOSTNAME} = 0;
delete $ENV{COMMANDER_HTTP_PROXY};

$SIG{__WARN__} = sub {
  if ($_[0] !~ m!^Use of uninitialized value in string eq at .*?Moose/Meta/Attribute.pm!)
  {
    print STDERR $_[0];
  }
};

my $commander = $ENV{COMMANDER_SERVER};
# Just backslash
my $bsl = $commander ? '' : '\\';
# semi-colon backslash
my $sc_bsl = $commander ? '' : ';\\';

my $windows_resource_prop = 'WindowsResource';
my $ec = Ecloud::Ec->new_with_options;

die $ec->err if $ec->err;

my $build_user_default = getpwuid($<);

if ($commander)
{
  my $launched_by = $ec->Get('/myJob/launchedByUser')->value;
  if ($launched_by !~ /:/)
  {
    # not project
    $build_user_default = (split '@', $launched_by)[0];
  }
}

my @opt_par = (                   [ 'input=s',
                                    "path to .ini file", {default => 'ci.ini'},
                                    {
                                     callbacks => {
                                                   'Must point to an existing file' => sub {
                                                     my $path = $_[0];
                                                     if ( !-f $path)
                                                     {
                                                       0;
                                                     } else
                                                     {
                                                       1;
                                                     }
                                                   }
                                                  }
                                    },
                                  ],
                                  ['build_user=s', "create clients for this user (for debugging)",  {default => $build_user_default}],
                                  [ 'output=s',
                                    "path to make file, defaults to STDOUT",
                                  ],
                                  [ 'branchName=s',
                                    "Build branch", {default => 'main'},
                                  ],
                                  [ 'job=s',
                                    "Job counter for debugging",
                                  ],
                                  [ 'project=s',
                                    "project name for debugging",
                                  ],
                                  [ 'procedure=s',
                                    "procedure name for debugging",
                                  ],
                                  [ 'platform=s',
                                    "Build for this platform only, by default build for all platforms",
                                  ],
                                  [ 'test_server!', "flag if test server"],
                                  [ 'trace!',
                                    "print disgnostic trace to STDERR", {default => 0},
                                  ],
                                  [ 'graph!',
                                    "flag to produce the graph in Storable format, else produce a makefile formatted output", {default => 0},
                                  ],
                                  ['arbitrate!', "Arbitrate CL's", {default => 1}],
                                  ['skip_apl!', "Skip APL (set when called from arbgitrate)",],
                                  [ 'help', 'Print usage message and exit', {shortcircuit => 1} ]
              );

my ( $options, $usage ) = eval {
  describe_options(
                   "%c %o", @opt_par
                  );
};

if ($@) {
  print $@;
  exit 1;
}

if ( $options->help ) {
  print $usage->leader_text . "\n";
  print $usage->option_text;
  exit;
}

printf "Running on %s\n", $ec->host if !$commander && !$options->graph;

my $skip_apl = $options->skip_apl;
my $build_user = $options->build_user;
my $genmake_name;
my $test_server = 0;

if (defined $options->test_server)
{
  $test_server = $options->test_server;
} else
{
  my $test_server_c = $ec->Get('/server/properties[test_server]');
  $test_server = $test_server_c->value if $test_server_c;
}

# Check for scriptdir if arbitratin
my ($arbitrate, $modules, $top, $scriptdir);
my $last_good_cl_value;
my $opt_cls;
my $dedicated_w_resource;
my $ignore_busy;
my $cl_user;
my $force_mods;
if ($options->arbitrate)
{
  my ( $options1, $usage ) = eval {
    my $cls_def = $commander ? `ectool getProperty /myJob/clSet` : '';
    chomp $cls_def;
    describe_options(
                     "%c %o",
                     ['ignorebusy!', "Ignore busy jobs (for debugging)", {default => $commander}],
                     ['cls=s',"Colon or comma separated list of CLs, for debugging", {default => $cls_def}], 
                     ['byuser=s',"Use CLS submitted by this user only", $commander && $ec->Get('/myJob/ClsByThisUserOnly')->value ? {default => $build_user} : ()],
                     ['genmake=s', 'genmake procedure name', {default => 'genmake-debug'}],
                     ['windows_resource=s', 'Name of the windows resource/pool to use',],
                     ['scriptdir=s',"Directory where the scripts are, required if arbitrating", 
                      $commander ? {default => $ec->Get('/myJob/properties[scriptDir]')->value } : {required => 1}],
                     [ 'last_good_cl=s', "Last Good CL to build against, for debugging", 
                       $commander ? {default => $ec->Get('/myJob/properties[lastGoodCL]')->value } : ()],
                    )
  };

  if ($@)
  {
    print $@;
    exit 1;
  }

  $arbitrate = 1;
  $scriptdir = $options1->scriptdir;
  $genmake_name = $options1->genmake;
  $opt_cls = $options1->cls;
  $last_good_cl_value = $options1->last_good_cl;
  $dedicated_w_resource = $options1->windows_resource;
  $ignore_busy = $options1->ignorebusy;
  $build_user = $cl_user = $options1->byuser;
} else
{
  my ( $options1, $usage ) = eval {
    describe_options(
                     "%c %o",
                     [ 'modules=s',
                       # 168959:dvm:rtl_build:rtl_build_vport:tb_build 168976:168973:168972:compiler:driver:ets:fs:ocl 168960:ts 168976:168973:168972:apitrace:compiler:driver:ets:fs:ocl
                       "list of space separated blocks to specify build targets, format: CL1[:CL2]:mod1[mod2][:CL...],",
                       {
                        required => 1},
                     ],
                     [ 'top=s',
                       "Name of the top target", {required => 1},
                     ],
                     [ 'last_good_cl=s',
                       "Last Good CL to build against", {required => 1},
                     ],
                     [ 'force_mods!', "Pretend we have mods(for debugging)"
                     ],
                    )
  };

  if ($@)
  {
    print $@;
    exit 1;
  }

  $force_mods = $options1->force_mods;

  $modules = $options1->modules;
  $top = $options1->top;
  $last_good_cl_value = $options1->last_good_cl;
  $scriptdir = $RealBin;
}

my $opt_platform = $options->platform;
my $trace;
my @last_rtl_targets;

my $project_name;
if ($commander)
{
  $project_name = $ec->Get('/myJob/properties[projectName]');
  die $ec->err if $ec->err;
  $project_name = $project_name->value;
} else
{
  $project_name = $options->project ? $options->project : die "project required when debugging"; ;
}

my $last_good_root = "/projects[$project_name]/properties[mods]/properties[$build_user]";
my %last_good_hash;
if (my @last_good_list = $ec->Get("$last_good_root/properties[]"))
{
  foreach my $p (@last_good_list)
  {
    last if !defined $p;
    my ($mod) = split('\.', $p->Name);
      
    $last_good_hash{$mod} = 1;
  }
}

my $job_name;
if ($commander)
{
  $job_name = $ec->Get('/myJob/properties[jobName]');
  die $ec->err if $ec->err;
  $job_name = $job_name->value;
} else
{
  $job_name = 'JOBNAME';
}

my $procedure_name;
if ($commander)
{
  $procedure_name = $ec->Get('/myJob/properties[procedureName]');
  die $ec->err if $ec->err;
  $procedure_name = $procedure_name->value;
} else
{
  $procedure_name = $options->procedure ? $options->procedure : die "procedure required when debugging";
}

my $postp = qq&postp --loadProperty /projects[$project_name]/procedures/[$procedure_name]/findError --require "PASSED" --ignore "ERROR"&;

my $job_counter;
if ($commander)
{
  $job_counter = $ec->Get("/projects[$project_name]/properties[jobCounter]");
  die $ec->err if $ec->err;
  $job_counter = $job_counter->value;
} elsif (!$arbitrate)
{
  $job_counter = $options->job ? $options->job : die "Job required when debugging";
}

my $default_artifact_version = get_artifact_version($job_counter);

my $in = $options->input;

$in = "$scriptdir/$in" if substr($in,0,1) ne '/';

open(IN, '<', $in) || die sprintf("Cannot open '%s' for reading:$!", $in);

my $output_prop_name = 'ci.ini';
if (!$arbitrate)
{
  if (defined $options->output)
  {
    open(OUT, '>', $options->output) || die sprintf("Cannot open %s for writing:$!", $options->output);
    if ($commander)
    {
      $ec->Create("/myJob/$output_prop_name", {value => $options->output});
    }
  } else
  {
    *OUT = *STDOUT;
  }
}

my $job_status_prop = '/myJob/properties[JobStepStatus]/properties';

my %last_good_targets;
my %client_roots;

my $graph = Graph->new;
$graph->set_graph_attribute(name => 'main');

$trace = $options->trace;

# Compute buildable 

# Set up modules map
my %buildable_modules;          # The ones that are in CLs
my @cl_set;
foreach my $chunk (split(' ', $modules))
{
  foreach my $d (split(':', $chunk))
  {
    if ($d =~ /^\d+$/)
    {
      push(@cl_set, $d);
      
    } else
    {
      $buildable_modules{$d} = ();
    }
  }
}

# Get the index
my %cl_ind;

my $cl_cnt = 0;
$cl_ind{$_} = $cl_cnt++ for @cl_set;

my $affected_modules = "@{[keys %buildable_modules]}";
my %client_info;                # Will hash stuff here
my $eval_target_file = "$scriptdir/eval_comb_result.pl";
my %group_hash;

my $rtl_only = 1;

# Very primitive parser
my @variant_vars = qw/platforms buildType target_arch sourcePath/;
my @artifacts_vars = qw/platforms buildType/;
my $nonvariant_vars = "buildScript";
my @must_build;
my %seen;

# Mapped means that the values cannot be used directly but rather via separate assignment, also they do not contribute to the artifacts
my @mapped_vars = qw/sourcePath target_arch/;
my %mapped_vars;
@mapped_vars{@mapped_vars} = ();

my @artifact_steps;

my %all_blocks;

{
  my %block;

  while (defined (my $line = <IN>))
  {
    chomp $line;

    if ($line =~ s/\\$//)
    {
      $line .= <IN>;
      redo unless eof(IN);
    }

    # Skip empty lines
    next if $line !~ /\S/;

    # Skip comment lines
    next if $line =~ /^\s*#/;

    # Accumulate blocks
    if ($line =~ /^\s*\[([^\]]+)/)
    {
      if (%block)
      {
        my %b = %block;
        $all_blocks{$block{goal}} = \%b;
        undef %block;
      }

      $block{__start} = $.;
      $block{goal} = $1;
      # Use graph 
      _add_vertex($graph, $block{goal});
      next;
    }

    # Split on name and value
    my ($name, $value) = $line =~ /^([^=]+)=(.*)/;
    # Strip leading and trailing spaces in name and value
    $name =~ s/\s//g;

    if ($name eq 'platforms' && $opt_platform)
    {
      if ($value =~ /$opt_platform/)
      {
        $value = $opt_platform;
      } else
      {
        next;
      }
    }

    $value =~ s/^\s*//;
    $value =~ s/\s*$//;

    $block{$name} = $value if $value;
  }

  # Save the last
  # Everything depends on apl NOT
  if ($block{goal} ne 'apl')
  {
    if (exists $block{parent})
    {
      $block{parent} .= ' apl';
    } else
    {
      $block{parent} = 'apl';
    }
  }

  my %b = %block;

  $all_blocks{$block{goal}} = \%b;
}

my $cygwin_shell = get_cygwin_top() . '\bin\bash --login -i';
#'C:\\cygwin64';

my %needed;
my %needed_platforms;
if ($modules =~ /TEST/)
{
  delete $buildable_modules{TEST};
  foreach my $key (keys %all_blocks)
  {
    if ($all_blocks{$key}->{buildKind} eq 'test')
    {
      $needed{$key} = ();
      _add_vertex($graph, $key);
      # Add parents of the test
      foreach my $p (split(' ', $all_blocks{$key}->{parent}))
      {
        if (!$graph->has_vertex($p))
        {
          _add_vertex($graph, $p);
        }
        _add_edge($graph, $p, $key);
        $needed{$p} = ();
      }
    }
  }
}

# And children
foreach my $v ($graph->vertices)
{
  # get rid of no platform
  # if (!exists $all_blocks{$v}->{platforms})
  # {
  #   _delete_vertex($graph, $v);
  #   delete $all_blocks{$v};
  #   next;
  # }

  if (exists $all_blocks{$v}->{parent})
  {
    foreach my $p (split(' ', $all_blocks{$v}->{parent}))
    {
      if (!$graph->has_vertex($p))
      {
        _add_vertex($graph, $p);
      }

      # And edge
      _add_edge($graph, $p, $v)
    }
  }
}

# Set up p4
# Read config.ini
my $config_ini = $scriptdir . '/config.ini';
open(IN, $config_ini) || die "Cannot open $config_ini for reading:$!";
  
my %config;
my $f;
while (defined (my $line = <IN>))
{
  if ($line =~ /^\[p4_server\]/)
  {
    $f++;
  } elsif ($line =~ /^\[/ && $f)
  {
    last;
  } elsif ($f)
  {
    my ($key, $val) = split('=', $line);
    $key =~ s/\s+//g;
    $val =~ s/\s+//g;
    $config{$key} = $val;
  }
}
  
close IN;

# Set up for P4
$ENV{P4PORT} = $config{P4PORT};
$ENV{P4USER} = $config{'P4USER' . ($test_server ? 'TEST' : '')};
$ENV{P4TICKETS} = $ENV{P4TICKETS_linux} = $ENV{P4TICKETS_windows} = $config{'P4TICKETSFILE' . ($test_server ? 'TEST' : '')};

$ENV{P4TICKETS_windows} =~ s!/home/ecagent!C:/Users/ecagent!; # hardcoded !!!

# Set cl sets
my $cl_stat_name = 'ClStatus';  # A hole here, this is used by findError, the name MUST match
my $cl_status_root = "/myJob/properties\[$cl_stat_name]/properties";
if ($commander)
{
  $ec->Create("$cl_status_root\[@cl_set]", {value => 0});
  die $ec->err if $ec->err;
} else
{
  print "CLS='@cl_set'\n" if !$options->graph;
}

# Make sure apl is first
process_block($all_blocks{apl =>});

if ($arbitrate) {
  foreach my $module ($graph->toposort)
  {
    process_block($all_blocks{$module});
  }
  arbitrate();
  exit;
} else
{

  if ($modules =~ /ALL/)
  {
    delete $buildable_modules{ALL};
    $buildable_modules{$_} = () for $graph->vertices;
  } 

  # Recods needed platforms
  foreach my $module (keys %buildable_modules)
  {
    foreach my $p (split(' ', $all_blocks{$module}->{platforms}))
    {
      $needed_platforms{$p} = ();
    }
  }
  
  # First all successors of buildable modules buildable as well
  foreach my $module (keys %buildable_modules)
  {
    foreach my $p ($graph->all_successors($module))
    {
      #    if ($all_blocks{$p}->{buildKind} eq 'test' && !exists $buildable_modules{$p})
      if (!exists $buildable_modules{$p})
      {
        $buildable_modules{$p} = ();
      }
    }
  }

  # Leave parents of the buildable modules only
  foreach my $module (keys %buildable_modules)
  {
    $needed{$_} = () for $graph->all_predecessors($module);
  }

  foreach my $module (keys %all_blocks)
  {
    if ($module ne 'apl' && !exists $needed{$module} && !exists $buildable_modules{$module})
    {
      delete $all_blocks{$module};
    }
  }
}

# Re-init graph
my $graph_copy = $graph->copy;
$graph = Graph->new;
$graph->set_graph_attribute(name => 'main');

my %buildable;
foreach my $s ($graph_copy->vertices)
{
  # Add successors of test modules if they are not available
  $buildable{$s} = () if $all_blocks{$s}->{buildKind} eq 'build';
}

my $graph_build_type = Graph->new;
foreach my $s (keys %buildable)
{
  _add_vertex($graph_build_type, $s);
  foreach my $ss (grep {exists $buildable{$_}} $graph_copy->all_predecessors($s))
  {
    _add_edge($graph_build_type, $ss, $s);
  }
}

my ($sync_rtl_build_target, $sync_rtl_source_target, $sync_rtl_build_target_command);

# Create a subgraph for rtl
my $rtl_graph = Graph->new;
$rtl_graph->set_graph_attribute(name => 'rtl');

foreach my $module ($graph_copy->toposort)
{
  next if ($skip_apl && $module eq 'apl') || !exists $buildable_modules{$module} && !exists $needed{$module};
  if (!process_block($all_blocks{$module})) {
    $DB::single = 1;
    1;
  }
}

if ($graph->has_a_cycle) {
  my @cycle = $graph->find_a_cycle;

  print STDERR "Disaster, DAG has a cycle<@cycle\n";
  exit 1;
}

# Add more if rtl_only
my @cl_order;
my $level;
if ($rtl_only && @cl_set > 1)
{
#  $trace=1;
  if ($commander)
  {
    # Set rtl only property to catch rtl error failures
    $ec->Create('/myJob/properties[rtlOnly]', {value => 1});
    die $ec->err if $ec->err;
  }
  if ((my $size = scalar(@cl_set) > MAX_NUM_COMB_TARGETS))
  {
    print STDERR "Trimming RTL cl_set from $size to @{[MAX_NUM_COMB_TARGETS]}\n" if !$options->graph;

    # Leave four max in cl list
    splice(@cl_set, MAX_NUM_COMB_TARGETS);

    # Trim cl_ind
    undef %cl_ind;
    my $cl_cnt = 0;
    $cl_ind{$_} = $cl_cnt++ for @cl_set;
  }

  # Create cl order
  @cl_order = map {"$_=$cl_ind{$_}"} keys %cl_ind;

  # Combinations

  my $depth = @cl_set;

  my $eval_target_stem = "combination_result";
  my $prev_eval_target = $eval_target_stem;
  my @rtl_graphs = $rtl_graph;

  # Take care of the already existing ...

  my $top_group = sprintf"CLs-%s", join('-', @cl_set);
  # Fix sync source target
  my $command = $graph->get_vertex_attribute($sync_rtl_source_target, command =>);
  $command =~ s/GENMAKE_GROUP=.*?\n//s;
  $command =~ s/GENMAKE_stepName=.*?\n/GENMAKE_stepName=source_client\n/s;
  
  check_group(\%group_hash, $sync_rtl_source_target, $command);
  $graph->set_vertex_attribute($sync_rtl_source_target, command => $command);
  
  my $cl_set_value = join('-', @cl_set);

  foreach my $v ($rtl_graph->vertices)
  {
    my $command = $graph->get_vertex_attribute($v, command =>);
    if ($v eq $sync_rtl_source_target)
    {
      $command =~ s/GENMAKE_GROUP=.*?\n//s;
      $command =~ s/GENMAKE_stepName=.*?\n/GENMAKE_stepName=source_client\n/s;
    } elsif ($v eq $sync_rtl_build_target)
    {
      $command =~ s/GENMAKE_GROUP=linux,rtl,sync/GENMAKE_GROUP=$top_group/s;
    } else
    {
      $command =~ s/GENMAKE_GROUP=linux,rtl(,?)/GENMAKE_GROUP=$top_group$1/s;
    }

    $command = qq&GENMAKE_condition="setProperty('/myJobStep/combinationIndex', 0);setProperty('/myJobStep/targetName', '$v');setProperty('/myJobStep/ClSets', '$cl_set_value')"
\t$command
&;

    check_group(\%group_hash, $v, $command);
    $graph->set_vertex_attribute($v, command => $command);

    if ($rtl_graph->has_vertex($v))
    {
      $rtl_graph->set_vertex_attribute($v, command => $command);
    }
  }

  # Also eval_target
  set_eval_target($eval_target_stem, [$rtl_graph], $top_group, join('-', @cl_set));

  my $targ_index = 1;
  foreach my $width (reverse 1..$depth-1)
  {
    $level++;
    my @chunk = combinations(\@cl_set, $width);
    printf STDERR "Level $level: %d combinations\n", scalar(@chunk) if !$options->graph;

    my @level_cl_sets;
    my @new_rtl_graphs;
    # Fix existing sync client vertices to limit cls
    my $rtl_client_name = get_client_name(rtl => linux =>);

    my $comb_property = "/myJob/runCombinations_$level";
    my $client_index = 0;
    foreach my $comb (@chunk)
    {
      push(@level_cl_sets, join('-', @$comb));

      # Will take care of the order later
      if ($commander)
      {
        # Record this combination
        $ec->Create("$cl_status_root\[@$comb]", {value => 0});
        die $ec->err if $ec->err;
      } else
      {
        print STDERR "Level $level: Adding '@$comb' to CLS\n" if !$options->graph;
      }

      # Duplicate rtl graph for this combo and level
      my $new_rtl_graph = Graph->new;
      $new_rtl_graph->set_graph_attribute(name => "cls-" . join('-', @$comb));
      push(@new_rtl_graphs, $new_rtl_graph);

      foreach my $v ($rtl_graph->vertices)
      {
        # Create a new target
        my $new_target = "$v" ."_$targ_index";

        # Massage the command
        my $command = $graph->get_vertex_attribute($v, command =>);

        # Add condition, Disable, will be enabled when prereqs fail
        $command =~ s&GENMAKE_condition=.*?\n&GENMAKE_condition="setProperty('/myJobStep/clSets', '@$comb');setProperty('/myJobStep/targetName', '$new_target');var result;if (getProperty ('$comb_property')){result = true} else {result = false;}result"\n&;

        _add_vertex($graph, $new_target);
        _add_vertex($new_rtl_graph, $new_target);

        my $new_rtl_client_name = $rtl_client_name . ($client_index ? "_$client_index" : ''); # Reuse main client
        # Replace client name in the command
        $command =~ s/$rtl_client_name/$new_rtl_client_name/gs;

        if ($v eq $sync_rtl_build_target)
        {
          # cls
          $command =~ s/cl_set=.*?\n/cl_set="@$comb"\n/s;

          # Make sure new clients are are in the dep chain
          # foreach my $l (@last_rtl_targets)
          # {
          #   my $nl = $l;
          #   if (my ($ind) = $new_target =~ /_(\d+)$/)
          #   {
          #     $nl =~ s/_(\d+)$//;
          #     $nl .= '_' . --$ind;
          #   }
          #   _add_edge($graph, $l, $new_target);
          # }
        }

        # Make it depend on the pervious layer
        _add_edge($graph, $prev_eval_target, $new_target);

        my $new_group = sprintf"Combination-$level,CLs-%s", join('-', @$comb);
        $command =~ s/GENMAKE_GROUP=.*?(,|\n)/GENMAKE_GROUP=$new_group$1/s;

        check_group(\%group_hash, $new_target, $command);

        $graph->set_vertex_attribute($new_target, command => $command);
        $new_rtl_graph->set_vertex_attribute($new_target, command => $command);

        # Depends on predecessors
        foreach my $p ($rtl_graph->predecessors($v))
        {
          my $new_p = $p . "_$targ_index";
          _add_edge($graph, $new_p, $new_target);
          _add_edge($new_rtl_graph, $new_p, $new_target);
        }

        # sinks must be added to the top
        if ($rtl_graph->is_sink_vertex($v))
        {
          _add_edge($graph, $new_target, $top);
        }

      }
      $client_index++;
      $targ_index++;
    }

    # Add new evauate
    my $eval_target = $prev_eval_target = "$eval_target_stem" . "_$level"; # And evaluation step
    my $new_group = "Combination-$level";
    set_eval_target($eval_target, \@new_rtl_graphs, $new_group, join(':', @level_cl_sets), $comb_property);
  }
}

my $resource = get_resource('linux');

my @command;
# Compute save last good
if (%last_good_targets)
{
  foreach my $module (keys %last_good_targets)
  {
    foreach my $variant (keys %{$last_good_targets{$module}})
    {
      push(@command, "\tectool setProperty 'mods/$build_user/$module.$variant/$job_counter' --value '@cl_set' --projectName $project_name");
    }
  }
}

my $set_last_good_command = join("\n\t", @command);

my $command = qq&GENMAKE_alwaysRun=1
\tGENMAKE_resourceName=$resource
\tall_cls="@cl_set"&;

# Set code to submit

# See if there are any combinations
if ($rtl_only)
{
$command .= qq&
\tgood_list="`ectool getProperty /myJob/goodCls`"
&;
} else
{
  # Submit all cls if the job succeeded
  $command .= qq&
\tstatus="`ectool getProperty /myJob/outcome`"
\tif [ \$\$status = 'success' -o \$\$status = 'warning' ] ; then
\t  good_list="@{[keys %cl_ind]}"
\tfi
&;
}

# Submit all cls succeeded and mask success
$command .= qq&\tif [ -n "\$\$good_list" ] ; then
\t$set_last_good_command
\t  for l in \$\$good_list; do
\t    echo Will submit CL \$\$l
\t  done
\t  ectool setProperty "/myJob/outcome" success
\tfi
\tif [ `expr length "\$\$all_cls"` -ne `expr length "\$\$good_list"` ] ; then
\t  for cl in \$\$all_cls ; do
\t    if [[ \$\$cl != "*\$\$all_cls*" ]] ; then
\t       echo Marking \$\$cl BAD
\t    fi
\t  done
\tfi
&;

$graph->set_vertex_attribute($top, command => "$command");

# Add top level target with user info
my $job_info_step = 'JobInformation';

my @leafs = $graph->predecessorless_vertices;
_add_vertex($graph, $job_info_step);

# Make all leaf nodes depend on it
_add_edge($graph, $job_info_step, $_) for @leafs;

# Make top depend on it
_add_edge($graph, $job_info_step, $top);


# Add cleanup target
# $graph->set_vertex_attribute(cleanup => command => "GENMAKE_alwaysRun=1
# \techo Client Cleanup done");

# Clear non-transitive
my $removed;

# Transitive edge for a vertex is en edge the end of which is also an end of some edges of its predecessors
my (%immediate_predecessors, %all_predecessors);
my $start = time();
foreach my $v ($graph->vertices)
{
  next if $graph->is_source_vertex($v);

  $immediate_predecessors{$v}->{$_} = () for $graph->predecessors($v);
  $all_predecessors{$v}->{$_} = () for $graph->all_predecessors($v);

}

# Now do it for sure
foreach my $v ($graph->vertices)
{
  next if !exists $immediate_predecessors{$v};

  foreach my $p (keys %{$immediate_predecessors{$v}})
  {
    next if !exists $all_predecessors{$p};
    foreach my $pp (keys %{$all_predecessors{$p}})
    {
      if (exists $immediate_predecessors{$v}->{$pp} && $graph->has_edge($pp, $v))
      {
        print STDERR "Deleting edge $pp : $v transitive via $p\n" if $trace;
        $graph->delete_edge($pp, $v);
        $removed++;
      }
    }
  }
}

if ($removed)
{
  printf STDERR "Removed $removed non-transitive edges in %d sec\n", time() - $start if $trace;
  #  exit 1;
}

# Compute summary
my $summary;
foreach my $cl (@cl_set)
{
  my $desc = `p4 describe $cl`;
  my ($build_user) = $desc =~ /Change\s+$cl\s+by\s+([^@]+)/;
  my $info = "$build_user:$cl";
  if (defined $summary)
  {
    $summary .= " $info";
  } else
  {
    $summary = "$info";
  }
}

my $total_summary = "<html> <b>$summary</b> <br> </br>Affected modules: <b><i> $affected_modules</i></b>";
if ($rtl_only)
{
  $total_summary .= "<br> </br>RTL only build with @{[$level+1]} combinations";
}

$total_summary .=  "</html>";
my $resource = get_resource('linux');

# Add command
$graph->set_vertex_attribute($job_info_step, command => qq&GENMAKE_resourceName=$resource
\tGENMAKE_stepName="Job Information"
\tectool setProperty "/myJobStep/summary" "$total_summary"
&
);

# Sanity checks, all goals MUST have commands
if (my @bad = grep {!$graph->has_vertex_attribute($_, command =>)} $graph->vertices)
{
  printf STDERR "The following vertices have no command set:\n%s\n", join("\n", @bad);
  exit 1;
}

# Create prop for total steps here
# 

my $release_windows_target = 'release_resource';

foreach my $v ($graph->toposort)
{
  
}

if ($commander)
{
  $ec->Create("$job_status_prop\[total]", {value => scalar($graph->vertices)});
}

if ($options->graph)
{
  store_fd($graph, *OUT) if $options->graph;
  print STDERR "Stored DAG in @{[$options->output]}\n" if $options->output;
  close OUT;
  exit;
} else
{
print_makefile($graph);
}

# Check if all targets have resource set
my $bad;
foreach my $v ($graph->vertices) {
  my $command = $graph->get_vertex_attribute($v, command =>);

  if ($command !~ /GENMAKE_resourceName=/s)
  {
    print "$v has no resource set\n";
    $bad++;
  }
}

exit 1 if $bad;

sub print_makefile {
  my ($this_graph) = @_;
# Print preamble
  print OUT <<'EOF';
# !!!!!!!!!!!! WARNING !!!!!!!!!!!!!!!!!!!!!
# This file is automatically generated
# Do not edit, your edits will be lost
# !!!!!!!!!!!! WARNING !!!!!!!!!!!!!!!!!!!!!


EOF

  # Define stuff for ec_utils 
  # Print rules

  # Print default target

#  print OUT ".DEFAULT_GOAL :=cleanup\n";
  print OUT ".DEFAULT_GOAL :=$top\n";

  print OUT "\n# RTL only build\n\n" if $rtl_only;

  # And variables
  print OUT "CL_SET := @cl_set\n";

  # shows in the correct order
  foreach my $v ($this_graph->toposort)
  {
    printf OUT "#TARGET\n$v: %s\n", join(' ', sort $this_graph->predecessors($v));
    print OUT "\t" . $this_graph->get_vertex_attribute($v, command=>) . "\n";

  }

  printf OUT "
# Total number of targets = %d
", scalar($this_graph->vertices);

}

# 
sub set_build_wsp_info {
  my ($moddata) = @_;

  my $module = $moddata->{goal};

  my %data;
  # Compute stuff
  my $cmd = ($scriptdir ? $scriptdir : $RealBin) . "/get_module_template.sh -m $module -b @{[$options->branchName]}";
  my $module_template = `$cmd`;
  
  if ($?)
  {
    print STDERR $module_template;
    print STDERR "Failed to find module template for $module\n";
    print STDERR "Used command '$cmd'\n";
    exit 1;
  }
  
  chomp $module_template;
  my %new_data;
  $new_data{template} = $module_template;

  $client_info{$module} = \%new_data;

#  $DB::single = 1;
  my @platforms = split(' ', $moddata->{platforms});
  foreach my $platform (@platforms)
  {
    foreach my $name (qw/source_client_name source_client_root build_client_name build_client_root/)
    {
      my $val = get_client_attribute($module, $platform, $name);

      $new_data{$platform}->{$name} = $val if defined $val;
    }
  }
  
}

sub fetch_artifact_command {
  my ($module, $parent, $variant, $platform, $last_good) = @_;

  my $client_path = get_client_root($parent, $platform);
  my $client_name = get_client_name($parent, $platform);

  my $group;

  my $cl_name = $client_name;
  substr($cl_name, -length($build_user) - 1) = '';
  if ($platform eq 'windows')
  {
    ($group) = (split('-', $cl_name))[-2];
  } else
  {
    ($group) = $cl_name =~ /-([^-]+)$/;
  }

  if ($module eq 'castor')
  {
    $variant = 'release';
  }

  my $artifact_version = $last_good ? get_artifact_version($last_good) : $default_artifact_version;

  my $shell = $platform eq 'linux' ? '/bin/bash -l' : $cygwin_shell;
  my $resource = get_resource($platform);

  my $p = ucfirst($module);
  my $command = qq&GENMAKE_shell='$shell'
\tGENMAKE_GROUP=$platform,$group
\tGENMAKE_stepName=Fetch${p}Artifacts
\tGENMAKE_resourceName=$resource
\tif [ -n "\$(DONT_CLOBBER_CLIENT)" ] ; then
\t  echo Skipping ...
\t  exit 0
\telse
\tectool --debug 1 retrieveArtifactVersions --artifactVersionName 'APL:$module-$variant:$artifact_version' \\
\t 	--overwrite "update" \\
\t 	--repositoryNames "default" \\
\t 	--toDirectory '$client_path'
\tectool setProperty "/myJobStep/summary" "Fetched APL:$module-$variant:$artifact_version"
\tfi
&;

  return $command;

}

sub wsp_root {
  my ($platform) = @_;

  my $root = ($platform eq 'linux' ? '/ec_test/work/hw-sw-ci' : 'C:/EC/builds');

  return $root;
}

sub get_client_attribute {
  my ($module, $platform, $name) = @_;

  #source_client source_client_root build_client build_client_root
  my $result;
  if ($name eq 'source_client_name')
  {
    # Only append platform to windows
    my $module_template = get_client_template($module, $platform);
    my $res = 'ec_' . ($test_server ? 'stg' : 'prod') . '_' . $options->branchName . '-';
    if (index($module_template,'rtl_template') != -1) {
      # rtl
      $res .= 'rtl';
    } elsif (index($module_template,'smoke_template') != -1)
    {
      $res .= 'smoke';
    } else
    {
      $res .= $module;
    }
    $res .= "-$platform"if $platform ne 'linux';
    return $res . "_$build_user";
  } elsif ($name eq 'source_client_root')
  {
    my $root = wsp_root($platform);
    my $sep = '/';
  
    my $dirname = get_client_attribute($module, $platform, source_client_name =>);
    return $root . $sep . $dirname;
  }  elsif ($name eq 'build_client_name')
  {
    my $source_name = get_client_attribute($module, $platform, source_client_name =>);
    if ($module ne 'apl')
    {
      # build client is the source client for apl
      my $module_template = get_client_template($module, $platform);

      if (index($module_template,'rtl_template') != -1)
      {
        $module = 'rtl';
      } elsif (index($module_template,'smoke_template') != -1)
      {
        $module = 'smoke';
      }
      $source_name =~ s/-$module/-build-${module}/;
    }
    return $source_name;
  } elsif ($name eq 'build_client_root')
  {
    return undef if $module eq 'apl'; # No build client for apl
    my $root = wsp_root($platform);
    my $sep = '/';
    my $dirname = get_client_attribute($module, $platform, build_client_name =>)  . $sep . join($sep, qw/sgpu main/);
    return $root . $sep . $dirname;
  } elsif ($name eq 'client_top')
  {
    my $root = wsp_root($platform);
    my $sep = '/';
    return $root . $sep . get_client_attribute($module, $platform, source_client_name =>);
  } elsif ($name eq 'build_client_top')
  {
    return undef if $module eq 'apl'; # No build client for apl
    my $root = wsp_root($platform);
    my $sep = '/';
    my $dirname = get_client_attribute($module, $platform, build_client_name =>);
    return $root . $sep . $dirname;
  }
  else
  {
    die "Unknown client attribute $name";
  }

  return $result;
}

sub save_artifact_command {
  my ($block, $variant, $platform) = @_;

  my $module = $block->{goal};
  my $from = get_client_root($module, $platform);
  my $shell = $platform eq 'linux' ? '/bin/bash -l' : $cygwin_shell;

  my $resource = get_resource($platform);
  my $group = "$platform,$module";
#  $group =~ s/$platform\.//;
  my $patterns = $block->{artifacts_patterns};
  replace_variables(\$patterns, $variant, $block);

  # Fix patterns for apitrace, don't ask me why !!
  if ($module eq 'apitrace')
  {
#    $patterns = lc($patterns);
  }
  # Artifact patterns are for some reason lower cased under _build
#  $patterns =~ s/(_build(?:[^;]+);?)/lc($1)/ge;

  my $p = ucfirst($module);
  my $step_name;
  if ($module eq 'castor')      # More hack
  {
    my $v = $variant;
    $v =~ s/$platform\.//;
    $v = ucfirst($v);
    $step_name = "Save${p}${v}Artifacts";
  } else
  {
    $step_name = "Save${p}Artifacts";
  }

  my $command = qq&GENMAKE_shell='$shell'
\tGENMAKE_resourceName=$resource
\tGENMAKE_GROUP=$group
\tGENMAKE_stepName=$step_name
& .
q&	echo Building $@ from $^; & . qq&
\tectool --debug 1 publishArtifactVersion --artifactName 'APL:$module-$variant' \\
\t	--compress 1 \\
\t	--followSymlinks 1 \\
\t	--repositoryName 'default' \\
\t	--fromDirectory '$from' \\
\t	--includePatterns '$patterns' \\
\t	--version '$default_artifact_version'
\tectool setProperty lastGoodCl --value $last_good_cl_value --artifactVersionName 'APL:$module-$variant:$default_artifact_version'
&;
  replace_variables(\$command, $variant, $block);

  # artifacts_patterns are special, cmake makes buildtyle under _build lowercase, I don't know why!!!
  
  return $command;

}

sub sync_client_command {
  my ($module, $platform, $source, $cl_set) = @_;

  # Create client if needed

  my $client_name = get_client_name($module, $platform, $source);

  # Add group
  my $group;

  # Get rid of the user
  my $cl_name = $client_name;
  substr($cl_name, -length($build_user) - 1) = '';
  if ($platform eq 'windows')
  {
    ($group) = (split('-', $cl_name))[-2];
    $client_name .= '_$$COMPUTERNAME';
  } else
  {
    ($group) = $cl_name =~ /-([^-]+)$/;
  }

  my $client_root = get_client_root($module, $platform, $source);
  # Save client root for cleanup
  push(@{$client_roots{$platform}}, $client_root) if !$source;
  my $client_template = get_client_template($module, $platform);
  my $top_root = $source ? get_client_top($module, $platform) : get_build_client_top($module, $platform);
  my $windows = $platform eq 'windows' ? 'windows' : '';

  my $shell = $platform eq 'linux' ? '/bin/bash -l' : 'C:\cygwin64\bin\bash --login';
  my $resource = get_resource($platform);

  my $step_name = ($source ? 'source' : 'build') . '_client';

  # Start building the command
  my $ticket = $ENV{"P4TICKETS_$platform"};

  my $step_name = $source ? 'source_client' : 'build_client';
  my $command = qq&GENMAKE_shell='$shell'
\tGENMAKE_resourceName=$resource
\tGENMAKE_stepName=$step_name
\tGENMAKE_GROUP=$platform,$group,sync
& .
q&	set -e& .
qq&
\texport CYGWIN=winsymlinks:nativestrict
&;
  if (!$source)
  {
    $command .= qq&\tif [ -n "\$(DONT_CLOBBER_CLIENT)" ] ; then
\t  echo Skipping ...
\t  exit 0
\telse
&;
  }
$command .= qq&\tif [ ! -e $client_root ] ; then
\t  force="-f"
\tfi
\tmkdir -p $client_root 
\tcd $top_root
\techo P4PORT=$ENV{P4PORT} > $client_root/.p4config 
\techo P4CLIENT=$client_name >> $client_root/.p4config 
\tcd $client_root
\texport P4TICKETS="$ticket"
\texport P4USER="$ENV{P4USER}"
\texport P4PORT="$ENV{P4PORT}"
\texport P4CLIENT="$client_name"
\tp4 client -t $client_template -o $client_name | sed -r -e "s@^Root:.*\@Root:	$client_root@"  \\
\t-e 's/^Host:.*//' -e 's/unlocked//' -e 's/locked//' | \p4 client -i  &;

  # Link build client top to apl
  if (!$source && $module ne 'apl')
  {
    my $apl_root = get_client_root(apl =>$platform, 1);
    $command .= 
qq&
\tif [ ! -e $top_root/apl ] ; then  
\t  echo Will link $top_root/apl to $apl_root 
\t   (cd $top_root; ln -s $apl_root apl) 
\tfi&;
  }

# Clobber the client if this is a build client
  if (!$source || $module eq 'apl')
  {
    my $source_client_root = get_client_root($module, $platform, 1);
    # Do not clobber apl, just unshelve
    if ($module ne 'apl')
    {
      my $cprs_args = "$source_client_root/* $client_root";
      if ($platform eq 'windows')
      {
        $cprs_args =~ s!(.):!/cygdrive/$1!g;
      }
      $command .= qq& 
\techo Clobbering client $client_name at $client_root 
\ttime /bin/rm -rf $client_root/* 
\tcd $client_root 
\techo Linking to source client
\ttime /bin/cp -rs $cprs_args
\techo reverting build client $client_name at $client_root&;
    } else
    {
      # Always revert apl
      $command .= "
\t p4 revert -w //...";
    }
    

    my $k = $module eq 'apl' ? '' : '-k';
    $command .= qq&
\techo syncing \$\$force $k build client $client_name at $client_root to CL $last_good_cl_value
\tp4 sync \$\$force $k //...\@$last_good_cl_value
&;
    if ($cl_set)
    {
      $command .= qq&\tcl_set="@$cl_set"
\techo Unshelving CLs \$\$cl_set into $client_name at $client_root
\tfor c in \$\$cl_set; do p4 unshelve -s \$\$c; done&;
      if ($module ne 'apl')
      {
        $command .= "
\tfi";
      }
    }
  } else
  {
    # Source client
    $command .=qq&
\techo Will sync \$\$force $client_name at $client_root to CL $last_good_cl_value
\tcd $client_root 
\tp4 sync \$\$force //...\@$last_good_cl_value
&;
  }

  return $command;

}

# Adds stuff to the graph
sub process_block {
  my ($this_block) = @_;

  # Process existing block
  if (!exists $this_block->{goal})
  {
    print STDERR "goal is missing on in block preceding line $.";
    return;
  }

  my $goal = $this_block->{goal};

  set_build_wsp_info($all_blocks{$goal});
  return 1 if $arbitrate;

  return 1 if $goal eq 'apl';

  if (!exists $this_block->{buildKind})
  {
    die "buildKind is missing on in block preceding line line $.";
  }

  # Compute build variants
  my @maps;
  my %mapped;

  my %reverse_vars;
  foreach my $v (@variant_vars)
  {
    next if !exists $this_block->{$v};
    my @vals = split(' ', $this_block->{$v});

    if ($v eq 'platforms')
    {
      @vals = grep {exists $needed_platforms{$_}} @vals;
    }
    if (exists $mapped_vars{$v})
    {
      next if scalar(@vals) == 1;
      my @vals1;
      foreach my $vv (@vals)
      {
        my $vc = $vv;
        # Replace / with _ in the target name
        $vc =~ s!/!_!g;
        $mapped{$vc} = ();
        push(@vals1, $vc);
        #        print OUT "MAPPED_VARS += $vc\n";
        $reverse_vars{$vc}->{$v} = $vv;
      }
      push(@maps, \@vals1);
    } else
    {
      $reverse_vars{$_} = $v for @vals;
      push(@maps, \@vals);
    }
  }

  my @vars;

  if (@maps)
  {
    # Process stuff with variants
    NestedLoops([@maps], sub {
                  my $build_variant = join('.', @_); # Including mapped
                  my $variant;
                  my %vars = %$this_block;
                  $this_block->{reverse_vars} = \%reverse_vars;

                  if (%mapped)
                  {
                    # Excluding mapped 
                    $variant = join('.', grep {!exists $mapped{$_}} @_);
                  } else
                  {
                    $variant = $build_variant;
                  }

                  if (index($variant, 'linux' ) != -1)
                  {
#                    $variant = lc($variant);
#                    $_ = lc($_) for @_;
                  }

                  if ($this_block->{buildKind} eq 'rtl')
                  {
                    process_rtl_block($this_block, $variant, @_);
                    return;
                  } elsif ($this_block->{buildKind} eq 'test')
                  {
                    process_test_block($this_block, $variant, @_);
                    return;
                  } elsif ($this_block->{buildKind} eq 'build')
                  {

                    process_build_block($this_block, $variant, @_);
                    return;
                  }
                });
  } else
  {
    # Without variants
    if ($this_block->{buildKind} eq 'rtl')
    {
      process_rtl_block($this_block);
    }
  }

  return 1;

  #  print OUT "\$(eval \$(call add_goal,$goal))\n";
}

sub process_test_block {
  my $this_block = shift;
  my $real_variant = shift;

  my $goal = $this_block->{goal};
  my $build_variant = join('.', @_); # Including mapped, may be empty

  my $module = $this_block->{goal};

  my $platform;

  # target may be variant
  if ($build_variant)
  {
    # Find the platform
    $platform = get_platform($this_block, $build_variant);
  }

  # Rule for each test
  my $resource = get_resource($platform);

  # last good for the parent depend on it if the parent is buildable
  foreach my $p (split(' ', $this_block->{parent}))
  {
    if (exists $buildable_modules{$p} && $all_blocks{$p}->{buildKind} eq 'build') {
      $last_good_targets{$p}{$real_variant} = ();
    }
  }

  # All targets depend on parent artifacts
  my $group = "$platform,smoke,$module";

  foreach my $test (split(' ', $this_block->{test}))
  {
    my $targ = "$goal.$build_variant.$test";
    _add_vertex($graph, $targ);

    # Add parent artifacts
    process_first_block_target($this_block, $real_variant, $platform, $targ);

    # Command
    my $client_path = get_client_root($goal, $platform);
    my $client_root = get_build_client_top($goal, $platform);
    my $test_script = $this_block->{testcommand};
    my $test_interpreter = substr((split(' ', $test_script))[0],-3) eq '.py' ? 'python' : '';
    my $command = qq&GENMAKE_resourceName=$resource
\tGENMAKE_GROUP=$group
\tGENMAKE_stepName=$test
\tGENMAKE_postProcessor='$postp'
&;
    if ($platform eq 'linux')
    {
      $command .= qq&\tGENMAKE_shell='/bin/bash -l'
\texport SGPU_ROOT=$client_root
\tbsub -q ec_smoke -I $test_interpreter $client_path/$test_script
&;
    } else
    {
      $client_root =~ s!/!\\!g;
      $client_path =~ s!/!\\!g;
      my $path = "$client_root\\apl\\extern\\tools\\windows\\x86\\python\\2.7.5\\;\%Path\%";
      $command .= qq&	set SGPU_ROOT=$client_root
	set PATH=$path
	cd $client_path
	$test_interpreter $test_script
&;
    }

    # Replace variables
    # This is horrible
    $command =~ s/\$test/$test/s;

    replace_variables(\$command, $build_variant, $this_block);
    $graph->set_vertex_attribute($targ, command => $command);
    _add_edge($graph, $targ, $top); # ANd top

#    add_cleanup_target('smoke', $platform, $targ);
  }
}

sub process_rtl_block  {
  my $this_block = shift;
  my $real_variant = shift;

  my $goal = $this_block->{goal};

  # Remember first target for combinations
  my $build_variant = join('.', @_); # Including mapped, may be empty

  # Create All dut targets 
  my $dut_val = $this_block->{dut};

  my $platform;

  # target may be variant
  if ($build_variant)
  {
    # Find the platform
    $platform = get_platform($this_block, $build_variant);
  }

  $platform = 'linux' if !defined $platform;

  my $last_target;
  foreach my $dut (split(' ', $dut_val))
  {
    my $targ_stem = "$goal";
    $targ_stem .= ".$platform" if $platform;

    $targ_stem .= ".$dut";

    # Always run build target
    my $build_target = $last_target = "$targ_stem.run_build";
    _add_vertex($graph, $build_target);

    # And to rtl graph
    _add_vertex($rtl_graph, $build_target);

    my $step_name = $this_block->{testcommand} ? 'build' : $dut;
    my $group = "$platform,rtl,$goal";
    $group .= ",$dut" if $this_block->{testcommand};

    # They are all parallel
    process_first_block_target($this_block, $real_variant, $platform, $build_target);

    # Command
    my $client_path = get_client_root($goal, $platform);
    my $shell = $platform eq 'linux' ? '/bin/bash -l' : $cygwin_shell;

    my $client_name = get_client_name($goal, $platform);

    my $ticket = $ENV{"P4TICKETS_$platform"};
    my $resource = get_resource('linux');
    my $command = qq&GENMAKE_postProcessor='$postp  --property $cl_stat_name="@cl_set"'
\tGENMAKE_resourceName=$resource
\tGENMAKE_shell='$shell'
\tGENMAKE_GROUP=$group
\tGENMAKE_stepName=$step_name
\tsource \$\$ESCHER_ROOT/conf/prod/.bashrc.escher-de
\t$client_path/\$scriptpath/\$buildcommand $dut $client_path/\$datapath $client_path/\$scriptpath '$job_name' 'EC' 'smoke' $last_good_cl_value
&;

    # Replace variables
    replace_variables(\$command, $build_variant, $this_block);
    $command =~ s!//!/!gs;

    # Set command
    $graph->set_vertex_attribute($build_target, command => $command);

    if ($this_block->{testcommand})
    {
      my $test_target = $last_target = "$targ_stem.run_test";
      _add_vertex($graph, $test_target);
      _add_edge($graph, $build_target, $test_target);

      # And to rtl graph
      _add_vertex($rtl_graph, $test_target);
      _add_edge($rtl_graph, $build_target, $test_target);

      my $test_arg;

      if (exists $this_block->{tests} )
      {
        # Hack again!!
        $test_arg = $this_block->{tests};
        $test_arg =~ s/\$\(DUT\)/$dut/;
      } else
      {
        $test_arg = 'NULL';
      }

      my $test_command = qq&GENMAKE_postProcessor='$postp  --property $cl_stat_name="@cl_set"'
\tGENMAKE_resourceName=$resource
\tGENMAKE_shell='$shell'
\tGENMAKE_GROUP=$group
\tGENMAKE_stepName=test
\t$client_path/\$scriptpath/\$testcommand \\
\t$dut \\
\t$client_path/\$datapath \\
\t$client_path/\$scriptpath \\
\t$test_arg \\
\t'$job_name' \\
\t'EC' \\
\t'smoke' \\
\t$last_good_cl_value
&;
      replace_variables(\$test_command, $build_variant, $this_block);
      
      $command =~ s!//!/!gs;
      # Set command
      $graph->set_vertex_attribute($test_target, command => $test_command);
    } else
    {
      _add_edge($graph, $build_target, $top); # Make top depend on it
    }

    _add_edge($graph, $last_target, $top); # Make top depend on it
    push(@last_rtl_targets, $last_target);

#    add_cleanup_target('rtl', $platform, $last_target);
  }

}

sub sync_build_module {
  my ($module, $dep, $platform) = @_;

  my $client_name = get_client_name($module, $platform);

  my $targ = "sync_$client_name";

  my $is_rtl = $all_blocks{$module}->{buildKind} eq 'rtl';

  # Add vertex
  if (!$graph->has_vertex($targ))
  {
    _add_vertex($graph, $targ);
    if ($is_rtl)
    {
      # And to rtl graph
      _add_vertex($rtl_graph, $targ);
    }

    # Depends on the source sync
    my $source_sync = sync_source_module($module, $platform);

    _add_edge($graph, $source_sync, $targ);

    if (!$skip_apl)
    {
      # Depends on apl source module
      my $apl_mod = sync_source_module('apl', $platform);
      _add_edge($graph, $apl_mod, $targ);
    }

    # Command
    my $command = sync_client_command($module,$platform,0,\@cl_set);

    $graph->set_vertex_attribute($targ, command => "$command");

    $sync_rtl_build_target = $targ if $targ =~ /-build-rtl$/;
  }

  # Dep depends on it
  _add_edge($graph, $targ, $dep);

  if ($is_rtl)
  {
    # And to rtl graph
    _add_edge($rtl_graph, $targ, $dep);
  }

  return $targ;
}

sub sync_source_module {
  my ($module, $platform) = @_;

#  $DB::single = 1;

  my $client_name = get_client_name($module, $platform,1);
  my $targ = "sync_$client_name";
  if (!$graph->has_vertex($targ))
  {
    $sync_rtl_source_target = $targ if $all_blocks{$module}->{buildKind} eq 'rtl';

    _add_vertex($graph, $targ);
    # Command
    my $command = sync_client_command($module, $platform, 1);

    $graph->set_vertex_attribute($targ, command => $command);

    # For windows add a step to grap the resource
    if ($platform eq 'windows')
    {
      my $grab_resource_targ = 'reserve_windows_resource';
  
      if (!$graph->has_vertex($grab_resource_targ))
      {
        _add_vertex($graph, $grab_resource_targ);

        # Command
        my $w_prop = 'windows';
        if ($commander)
        {
          if (my $w_resource = $ec->Get("/myJob/properties[$windows_resource_prop]")) 
          {
            if ( my $w = $w_resource->value) {
              $w_prop = $w;
            }
          }
        }
        $graph->set_vertex_attribute($grab_resource_targ, command => qq&\tGENMAKE_exclusive=1
\tGENMAKE_GROUP=windows
\tGENMAKE_resourceName=$w_prop
\tGENMAKE_stepName=reserve_resource
\tectool setProperty "/myJob/$windows_resource_prop" \%COMMANDER_RESOURCENAME\%&)
      }

      _add_edge($graph, $grab_resource_targ, $targ);
    }
  }

  return $targ;
}

sub get_build_client_top {
  my ($module, $platform) = @_;
  
  get_client_attribute($module, $platform, build_client_top =>);

}

sub get_client_name  {
  my ($module, $platform, $source) = @_;

  my $res = get_client_attribute($module, $platform, ($source ? 'source' : 'build') . '_client_name');
  if ($platform eq 'windows')
  {
#    $res .= '_$$COMPUTERNAME';
  }
  return $res;
}

sub get_client_root  {
  my ($module, $platform, $source) = @_;

  get_client_attribute($module, $platform, ($source ? 'source' : 'build') . '_client_root')
}

sub get_client_top {
  my ($module, $platform) = @_;

  get_client_attribute($module, $platform, client_top =>);
}

sub get_client_template {
  my ($module, $platform) = @_;
  $client_info{$module}->{'template'} . ($module eq 'apl' || $module eq 'ocl' ? "_$platform" : '');
}

sub fetch_artifact {
  my ($block, $variant, $platform, $dep) = @_;

  my $parent = $block->{parent};
  my $module = $block->{goal};

  # We fetch into a client, not the target
  my $client = get_client_name($module, $platform);
  $client =~ s/.+-build-//;

  my %fetch_targets;
  foreach my $p (split(' ', $parent))
  {
    if ($p eq 'apl')
    {
      # If depends on client sync as well NOT
#      sync_build_module($module, $dep, $platform) if !$skip_apl;
      next;
    }

    my $targ = "$p.$variant.artifacts.for.$client";

    # Recods targets for later
    push(@{$fetch_targets{$p}}, $targ);

  }

  foreach my $m (keys %fetch_targets)
  {
    next if !exists $fetch_targets{$m};
    # Leave tops only
    foreach my $p ($graph_build_type->predecessors($m))
    {
      delete $fetch_targets{$p};
    }
  }

  my $is_rtl = $block->{buildKind} eq 'rtl';

  foreach my $p (keys %fetch_targets)
  {
    my $targ = "$p.$variant.artifacts.for.$client";

    my $parent_block = $all_blocks{$p};
    # Add the vertex if not there

    # Skip parents of test targets that have no matching platform
    if ($block->{buildKind} eq 'test')
    {
      if (index($parent_block->{platforms}, $platform) == -1)
      {
        next;
      }
    }
    if (!$graph->has_vertex($targ))
    {
      _add_vertex($graph, $targ);

      # And to rtl graph
      if ($is_rtl)
      {
        _add_vertex($rtl_graph, $targ);
      }

      # If depends on client sync as well
      sync_build_module($module, $targ, $platform);

      # Depends on parent artifacts
      # Save last good if any
      my $parent_last_good = exists $parent_block->{last_good}->{$variant} ? $parent_block->{last_good}->{$variant} : undef;

      if (!$parent_last_good)
      {
        my $p_artifact_module = save_artifact($all_blocks{$p},$variant,$platform);
        _add_edge($graph, $p_artifact_module, $targ);

        # And to rtl graph
        if ($is_rtl)
        {
          _add_edge($rtl_graph, $p_artifact_module, $targ);
        }
      }

      my $command = fetch_artifact_command($p,$module, $variant,$platform,$parent_last_good);
      $graph->set_vertex_attribute($targ, command => $command);
    }

    # dep depends on it
    _add_edge($graph, $targ, $dep);

    # And to rtl graph
    if ($is_rtl)
    {
      _add_edge($rtl_graph, $targ, $dep);
    }
  }
} 

sub save_artifact {
  my ($block,$variant,$platform) = @_;

  my $goal = $block->{goal};
  if ($goal eq 'castor')
  {
    $variant = 'release';
  }
  my $targ = "$goal.$variant.artifacts";

  if (!$graph->has_vertex($targ))
  {
    _add_vertex($graph, $targ);

    # Add command
    $graph->set_vertex_attribute($targ, command => save_artifact_command($block, $variant,$platform));

    # Make cleanup depend on it
#    add_cleanup_target($goal, $platform);
  }

  return $targ;
}

sub _delete_edge {
  my $graph = shift;

  my $name = $graph->get_graph_attribute(name =>) || 'UNKNOWN';

  print STDERR "$name: deleting edge $_[1]: $_[0] ...\n" if $trace;
  $graph->delete_edge(@_);
}

# To catch cycles
sub _add_edge {
  my $graph = shift;
  if (!$_[0] || !$_[1])
  {
    $DB::single = 1;
    return;
  }

  if ($_[0] eq $_[1])
  {
    $DB::single = 1;
    return;
  }

  my $name = $graph->get_graph_attribute(name =>) || 'UNKNOWN';

  print STDERR "$name: Adding edge $_[1]: $_[0] ...\n" if $trace;

  if ($_[1] =~ /artifacts$/ && $_[0] =~ /target_paths$/ && (split('\.', $_[0]))[0] ne (split('\.', $_[1]))[0])
  {
#    $DB::single = 1;
    1;
  }

  $graph->add_edge(@_);

  if ($trace && $graph->has_a_cycle)
  {
    my @cycle = $graph->find_a_cycle;
    print STDERR "!!!Cycle <@cycle>\n";
    $DB::single = 1;
    exit 1;
  }

  $graph;
}

sub get_cygwin_top {
  my $client_top = get_client_top('apl', 'windows');
  my $windows_path = "$client_top/extern/tools/windows/x86/cygwin/1.7.21-0";
  $windows_path =~ s!/!\\!g;

  return $windows_path;
}

sub process_build_block {
  my $this_block = shift;
  my $real_variant = shift;

  my @build_commands = split(':', $this_block->{build_commands});

  my $start = $this_block->{__start};

  my $i = 0;
  foreach my $chunk (@build_commands)
  {
    if (index($chunk,"=") == -1)
    {
      $DB::single = 1;
      print STDERR "Syntax error, cannot find '=' in <$chunk>(#$i) from '@build_commands', starting at line $start\n";
      exit 1;
    }
    $i++;
  }

  my $goal = $this_block->{goal};
  my $build_variant = join('.', @_); # Including mapped
  return if $goal eq 'dvm' && $build_variant =~ /release/; # Hacking galore !!!

  # Find the platform
  my $platform = get_platform($this_block, $build_variant);

  # If it is not buildable, maybe we can fetch
  if (!exists $buildable_modules{$goal})
  {
    my $g_variant = $real_variant;
    # Hack
    if ($goal eq 'castor')
    {
      $g_variant =~ s/release/relwithdebinfo/;
    }

    my $last_good = $force_mods ? '1234' : $ec->Get("$last_good_root/properties[$goal.$g_variant]/properties");
    if ($ec->err && $ec->err !~ /NoSuchProperty/)
    {
      die $ec->err;
    }

    $this_block->{last_good}->{$g_variant} = $last_good;
    if ($goal eq 'dvm')
    {
      # Hack
      my $r = $g_variant;
      $r =~ s/relwithdebinfo/release/;
      $this_block->{last_good}->{$r} = $last_good;
    }

    return if $last_good;



    $buildable_modules{$goal} = (); # Build it if fetch not available
  }

  # Figure rtl only
  if ($rtl_only && $platform eq 'linux')
  {
    my $t = get_client_template($goal, 'linux');

    if ($t !~ /rtl_template/)
    {
      undef $rtl_only;
    }
  }

  my $ind = 0;
  my $last_v;
  my $resource = get_resource($platform);

  # Make command target specific
  my $client_path = get_client_root($goal, $platform);

  foreach my $chunk (@build_commands) 
  {
    # Create a target
    my ($target_name, $target_command) = split('=', $chunk);
    # Clear blanks
    $target_name =~ s/\s+//g;
    $target_command =~ s/^\s+//;
    my $v = "$goal.$build_variant.$target_name";

    # Clear all blanks in the target name
    $v =~ s/\s//g;

    # Clear leading blanks in the command
    $target_command =~ s/^\s*//;

    # Add it
    _add_vertex($graph, $v);

    my $group = "$platform,$goal";

    my %reverse;

    if ($this_block->{reverse_vars} && %{$this_block->{reverse_vars}})
    {
      # Massage for linux
      my %r;
      if ($platform =~ /linux/)
      {
        foreach my $k (%{$this_block->{reverse_vars}})
        {
          my $kk = $k eq 'RelWithDebInfo' ? 'relwithdebinfo' : $k;
          $r{$kk} = $this_block->{reverse_vars}->{$k};
        }
      } else
      {
        %r = %{$this_block->{reverse_vars}};
      }

      foreach my $vv (split('\.', $build_variant))
      {
        next if exists $reverse{$vv};
        my $key = $r{$vv};
        if (ref($key))
        {
          my ($k, $v) = %$key;
          $reverse{$k} = $v;
          1;
        } else
        {
          $reverse{$key} = $vv;
        }
      }

      # First 
      foreach my $v (keys %reverse)
      {
        # Ignore single entry
        next if $this_block->{$v} !~ /\s/;
        if ($target_command =~ /\\?\$$v/s)
        {
          $group .= ",$reverse{$v}";
        }
      }

    }

#    $group =~ s/\./,/g;
    my $step_name = $target_name;

    my $shell = $platform eq 'linux' ? qq&GENMAKE_shell='/bin/bash -l'
\t& : "";
    my $command = qq&${shell}GENMAKE_resourceName=$resource
\tGENMAKE_postProcessor=postp
\tGENMAKE_GROUP=$group
\tGENMAKE_stepName=$step_name
\tcd $client_path
&;
    if ($platform eq 'linux')
    {
     $command .= "\t" . (exists $this_block->{queue} ? "bsub -q $this_block->{queue} -I " : '') . qq&$client_path/$target_command& . ($goal eq 'dvm' ? " $last_good_cl_value" : '') . "
";
   } else
   {
     my $l_command = "$client_path/$target_command";
     $l_command =~ s!(.):!/cygdrive/$1!g;
     my $client_top = get_build_client_top($goal, $platform);
     my $windows_path = get_cygwin_top();

     $command .= qq&\t\set SHELLOPTS=igncr
\tset CYGROOT_PARENT=$windows_path
\tset CHERE_INVOKING=1
\tif exist "C:\\Program Files (x86)\\Microsoft Visual Studio 11.0\\VC\\vcvarsall.bat" (
\t    call "C:\\Program Files (x86)\\Microsoft Visual Studio 11.0\\VC\\vcvarsall.bat"
\t) else if exist "C:\\Program Files\\Microsoft Visual Studio 11.0\\VC\\vcvarsall.bat" (
\t    call "C:\\Program Files\\Microsoft Visual Studio 11.0\\VC\\vcvarsall.bat"
\t) else (
\t    echo "Warning: fail in executing vcvarsall.bat"
\t)
\t$windows_path\\bin\\bash.exe --login -i $l_command
&;
   }

    # Replace variables
    replace_variables(\$command, $build_variant, $this_block);

    $graph->set_vertex_attribute($v, command => $command);

    # Add edge for all but the last
    if ($ind)
    {
      _add_edge($graph, $last_v, $v);
    } else
    {
      process_first_block_target($this_block, $real_variant, $platform, $v);

    }

    $last_v = $v;               # Capture last

    $ind++;
  }

  # Add artifacts if any
  my $a_goal;
  if (exists $this_block->{artifacts_patterns} && exists $buildable_modules{$goal})
  {
    # Artifacts for a buildable target
    my $a_targ = save_artifact($this_block, $real_variant, $platform, $last_v);

    # create step to save last good
#    my $last_good_cl_prop_step = last_good_targ($this_block, $real_variant, $platform);
#    my $targ = "$this_block->{goal}.$variant";

#    push(@last_good_targets,[$this_block->{goal}, $real_variant]);
    _add_edge($graph, $last_v, $a_targ);
    _add_edge($graph, $a_targ, $top);
  } else
  {
    _add_edge($graph, $last_v, $top)
  }
}

sub last_good_targ {

  my ($this_block, $variant, $platform) = @_;

  # Variant here contains platform.
  my $targ = "$this_block->{goal}.$variant.save_last_good";

#   if (!$graph->has_vertex($targ))
#   {
#     _add_vertex($graph, $targ, 0);

#     # Command
#     my $last_good = $job_counter;
#     my $group = "$platform,$this_block->{goal}";
# #    $group =~ s/\./,/g;
#     my $step_name = 'save_last_good';
#     my $command = "GENMAKE_GROUP=$group
# \tGENMAKE_stepName=$step_name";

#     $graph->set_vertex_attribute($targ, command => $command);
#   }
  return $targ;
}

sub process_first_block_target {
  my ($this_block, $real_variant, $platform, $dep) = @_;

  # First depends on TOP parent artifacts and client sync
  if (exists $this_block->{parent})
  {
    # get the artifacts, they will depend on client sync
    fetch_artifact($this_block, $real_variant, $platform, $dep);
  } else
  {
    # If depends on client sync as well
    sync_build_module($this_block->{goal}, $dep, $platform);
  }
}


sub get_platform {
  my ($this_block, $build_variant) = @_;

 OUTER:
  foreach my $pd (split('\.', $build_variant))
  {
    foreach my $pp (split(' ', $this_block->{platforms}))
    {
      if ($pd eq $pp)
      {
        return $pd;
      }
    }
  }

  die "Cannot find platform from $this_block->{platforms} in $build_variant";
}

sub replace_variables {
  my ($command, $variant, $block) = @_;

  # Leave relevant
  my %reverse;

  if ($block->{reverse_vars} && %{$block->{reverse_vars}})
  {
    # Massage for linux
    my %r;
    if ($variant =~ /linux/)
    {
      foreach my $k (%{$block->{reverse_vars}})
      {
        my $kk = $k eq 'RelWithDebInfo' ? 'relwithdebinfo' : $k;
        $r{$kk} = $block->{reverse_vars}->{$k};
      }
    } else
    {
      %r = %{$block->{reverse_vars}};
    }

    foreach my $vv (split('\.', $variant))
    {
      next if exists $reverse{$vv};
      my $key = $r{$vv};
      if (ref($key))
      {
        my ($k, $v) = %$key;
        $reverse{$k} = $v;
        1;
      } else
      {
        $reverse{$key} = $vv;
      }
    }
  }

  my %found;
  # First 
  foreach my $v (keys %reverse)
  {
    if ($$command =~ s/\\?\$$v/$reverse{$v}/gs) {
      $found{$v} = ();
    }
    1;
  }

  my %b = %$block;

  foreach my $v (keys %$block)
  {
    next if exists $found{$v};
    $$command =~ s/\\?\$$v/$b{$v}/gs;
  }
}

sub _add_vertex {
  my ($graph, $v, $platform) = @_;

  my $name = $graph->get_graph_attribute(name =>) || 'UNKNOWN';

  # Set attribute for shell
  print STDERR "$name: Adding vertex $v\n" if $trace;;
  $graph->add_vertex($v);
#  $graph->set_vertex_attribute($v, platform => ($platform ? $platform : 'linux'));
}

sub _delete_vertex {
  my ($graph, $v) = @_;

  # Set attribute for shell
  print STDERR "Deleting vertex $v\n" if $trace;;
  $graph->delete_vertex($v);
}

sub get_artifact_version {
  my ($tag) = @_;

  "1.0-$build_user" . "_$tag";
}

sub remove_transitive {
  my ($gobj) = @_;

  # Transitive edge for a vertex is en edge the end of which is also an end of some edges of its predecessors
  foreach my $v ($gobj->vertices)
  {
    my %h;
    foreach my $p ($gobj->all_successors($v))
    {
      $h{$p} = ();
    }

    foreach my $p (keys %h)
    {
      foreach my $pp ($gobj->all_successors($p))
      {
        if (exists $h{$pp})
        {
          print STDERR "Deleting edge $pp : $v transitive via $p\n" if $trace;
          _delete_edge($gobj, $pp, $v);
          $removed++;
        }
      }
    }
  }

  if ($removed)
  {
    print STDERR "Found $removed non-transitive edges !!!\n" if $trace;
    #  exit 1;
  }

}

sub get_resource {
  my ($platform) = @_;

  my $res;

  if ($platform eq 'linux') {
    $res = 'Arbitration_linux';
  } else
  {
    $res = qq&"\$\$& . qq&[/myJob/$windows_resource_prop]"&;
  }

  return $res;
}

sub arbitrate {
  my $this_job_id = '$[/myJob/jobId]';
  my $this_job_obj;

  # See if we are running
  if ($commander)
  {
    $this_job_id = $ec->Get('/myJob/properties[jobId]')->value;
    $this_job_obj = $ec->Get("/jobs[$this_job_id]");

    # Is there an arbitration job running?
    my $my_prop = "/projects[$project_name]/properties[arbitrationJob]";
    my $running_jobs = $ec->Get($my_prop);

    if ($ec->err && $ec->err !~ /NoSuchProperty/)
    {
      die $ec->err;
    }

    $DB::single = 1;

    my @jobs2leave = $this_job_id;
    my $blocked;
    if ($running_jobs)
    {
      foreach my $running_job_id (split(',', $running_jobs->value))
      {
        # See if it is active OR not idle
        if (my $job =  $ec->Get("/jobs[$running_job_id]"))
        {
          my $status = $job->status;
          my $name = $job->jobName;
          my $good = $job->Get('/properties[report-urls]');

          printf "Job $name has status $status\n";
          printf "Job $name has status $status and found %s\n", $good ? 'modules to build' : 'nothing' ;

          if ($status ne 'completed')
          {
            # Check if this job is an another arbitration job
            my $job_proc = $job->procedureName;
            my $job_proj = $job->projectName;
            if ($job_proj eq $project_name && $job_proc eq $procedure_name)
            {
              print "Job $name is an another arbitration job in progress\n";
              $blocked = $name;
            } else
            {
              push(@jobs2leave, $job->jobId);
              printf "Retaining job $name(%s)\n", $job->jobId;
            }
          } elsif (!$good)
          {
            printf "Deleting job $name(%s)\n", $job->jobId;
            $job->Remove;
          }
        }
      }
      $running_jobs->Modify({value => join(',', @jobs2leave)}) || die $running_jobs->err;
    }  else
    {
      $ec->Create($my_prop, {value => join(',', @jobs2leave)});
      die $ec->err if $ec->err;
    }

    printf "Set list to consider on the next run to %s\n", join(',', @jobs2leave);
    if ($blocked)
    {
      system(qq!ectool setProperty /myJobStep/summary "Blocked by job $blocked"!) if $commander;
      print("Blocked by $blocked\n") if !$commander;
      exit;
    }
  }

  my $cl_list;

  if ($opt_cls)
  {
    $cl_list = $opt_cls;
    $cl_list =~ s/,|:/ /g;
  } else
  {
#    my $db_script_name = 'db_shelvedclSet.py select';
    my $db_script_name = 'get_clSet_old.py --filter EC_TEST';
    my $db_command = $scriptdir . "/$db_script_name --branch @{[$options->branchName]} --test_server $test_server";
    if ($cl_user)
    {
      print "Will consider CLs tagged EC_TEST by $cl_user only\n";
      $db_command .= qq& --user "$cl_user" & if $cl_user;
    } else
    {
      print "Will consider CLs tagged EC_TEST by any user\n";
    }

    # Execute
    undef $!;
    print "Querying CL database...\n";
    $cl_list = `$db_command 2>&1`;
    if ($?)
    {
      print STDERR $cl_list if $cl_list;
      print STDERR "$db_command: $!\n" if $!;
      exit 1;
    }

    chomp $cl_list;
  }

  if ($cl_list)
  {
    print "Got CLs:$cl_list\n" if $cl_list;
  } else
  {
    print "No Pending CLs found\n";
    system('ectool setProperty "/myJobStep/summary" "No Pending CLs found"') if $commander;
    system('ectool setProperty "/myJob/Idle" "1"') if $commander;
    exit;
  }

  exit if !$cl_list;
  my %busy_modules;
  my $running_jobs_prop = "/projects[$project_name]/properties[runningJobs]";

  # Get job ID's
  print "Querying EC for $running_jobs_prop\n";
  my $jobs = $ec->Get($running_jobs_prop);

  if ($ec->err && $ec->err !~ /NoSuchProperty/)
  {
    die $ec->err;
  }

  if ($jobs)
  {
    foreach my $p ($jobs->Get('/properties[]'))
    {
      my $job_id = $p->Name;
      print "Examining jobId $job_id\n";

      # Do it
      my $job=  $ec->Get("/jobs[$job_id]");

      if ($job)
      {
        my $name = $job->jobName;
        my $status = $job->status;

        print "Found job $name with status=$status\n";

        if ($status ne 'completed')
        {
          foreach my $m (split(':', $p->value))
          {
            # This module is in progress, ignore
            printf "Found Busy module $m%s\n", $ignore_busy ? ',ignoring' : ''; 
            $busy_modules{$m} = $name if !$ignore_busy;
          }
          next;
        } 
        {
          print "job $name is completed, removing from running jobs\n";
        }
      } else
      {
        print "job $job_id is bogus, removing\n";
      }

      # Bogus entry, remove
      $p->Remove if $commander;
    }
  }

  printf "\tModules in progress=%s\n", join(',', keys %busy_modules) if %busy_modules;

  # Get all modules
  my %modules;
  $modules{$_} = () for keys %all_blocks;

  # Process each cl
  my %found_cls;
  my @cls = split(' ', $cl_list);

  # Reducing
  if ((my $size = scalar(@cls)) > MAX_NUM_TARGETS)
  {
    print STDERR "Trimming number of CLs from $size to @{[MAX_NUM_TARGETS]}\n";
    splice(@cls,MAX_NUM_TARGETS);
  }

  # Make sure CL's are in the right order

  my $apl_changed;
  my @module_list = ('apl', grep {$_ ne 'apl'} keys %modules);
 LOOP:
  foreach my $cl (@cls)
  {
    print "Analyzing $cl\n";

    # Test against each client, put apl first
    foreach my $mod (@module_list)
    {
      my $client;
      if (! $modules{$mod}) 
      {
        my $cmd = $scriptdir . "/get_module_template.sh -m $mod -b " . $options->branchName;

        my $client = `$cmd`;

        if ($?)
        {
          print STDERR $client if $client;
          print STDERR "$cmd: $!\n" if $!;
          exit 1;
        }

        chomp $client;
        $modules{$mod} = $client;

      }

      $client = $modules{$mod};

      next if exists $busy_modules{$mod};

      # Add dvm if needed
#      $found_cls{$cl}{dvm} = () if $need_dvm;


      # Run command
      print "\tTesting $mod ...";
      my $cmd = "p4 -c $client fstat -F isMapped //...\@=$cl";
      if (`$cmd`)
      {
        print "--$cl: $mod\n";
        $found_cls{$cl}{$mod} = ();

        if ($mod eq 'apl')
        {
          $apl_changed++;
          # Apl is special
          foreach my $k (qw/test extern/)
          {
            my $m = $client;
            $m =~ s/apl_template/apl_${k}_template/;
            # Run command
            my $cmd = "p4 -c $m fstat -F isMapped //...\@=$cl";
            if (`$cmd`)
            {
              if (%found_cls)
              {
                print "Stopping analysis since test/extern module changed and other modules registered\n";
                last;
              }
              if ($k eq 'test')
              {
                #Any change in //apl/tests/... has to trigger all software tests. The rest of CL's are ignored in this case
                # We will ignore if any modules selected already and will finish if 

                foreach my $m (keys %all_blocks)
                {
                  print "Module $m is BUSY (job $busy_modules{$m})\n" if exists $busy_modules{$m};
                  if ($all_blocks{$m}->{buildKind} eq 'test' && !exists $busy_modules{$m})
                  {
                    $found_cls{$cl}{$m} = ();
                  }
                }
              } else
              {
                #Any change in //apl/extern/tools OR //apl/extern/libs has to rebuild all SW modules. DVM is NOT a SW module
                foreach my $m (keys %all_blocks)
                {
                  if ($m ne 'dvm' && $all_blocks{$m}->{buildKind} eq 'build' && !exists $busy_modules{$m})
                  {
                    $found_cls{$cl}{$m} = ();
                  }
                }
              }
            }
          }
          last;                 # Finish
        }

        # Add all successors of predecessors that are not all good
        foreach my $pre ($graph->all_predecessors($mod))
        {
          next if exists $found_cls{$cl}{$pre};
          if (!$last_good_hash{$pre})
          {
            print "---Adding predecessor no_last_good $pre of $mod\n";
            $found_cls{$cl}{$pre} = ();

            # And all its successors
            foreach my $suc ($graph->all_successors($pre))
            {
              next if exists $found_cls{$cl}{$suc};
              print "---Adding successor $suc of $pre\n";
              $found_cls{$cl}{$suc} = ();
            }
          }
        }

        # Add successors
        $found_cls{$cl}{$_} = () for $graph->all_successors($mod);

        # Also add predecessors that have no last good
        foreach my $p ($graph->all_predecessors($mod))
        {
          if (!$last_good_hash{$p} && !exists $found_cls{$cl}{$p})
          {
            print "--adding predecessor $p with no last good available\n";
            $found_cls{$cl}{$p} = ();
          }
        }
      } else
      {
        print "--MISSED\n";
      }
    }
  }

  if (!%found_cls)
  {
    print "All modules are in progress..., Exiting\n";
    exit;
  }

  # See if we can clump together
 AGAIN:
  foreach my $cl1 (keys %found_cls)
  {
    my $data1 = $found_cls{$cl1};
    my $l1 = scalar(keys %$data1);
  LOOP:
    foreach my $cl2 (keys %found_cls)
    {
      next if $cl1 eq $cl2;

      my $data2 = $found_cls{$cl2};

      # We can clump together if at least one common key
      # Use the shortest first
      my ($h1, $h2) = ($l1 < scalar(keys %$data2)) ? ($data1, $data2) : ($data2, $data1);

      foreach my $m (keys %$h1)
      {
        if (exists $h2->{$m})
        {
          my $new_key = "$cl1:$cl2";
          printf "Clumping $new_key: %s\n", join(':', (keys %$h1, keys %$h2));
          $found_cls{$new_key}{$_} = () for (keys %$h1, keys %$h2);

          delete $found_cls{$cl1};
          delete $found_cls{$cl2};
          goto AGAIN;
        }
      }
    }
  }

  # Windows are single threaded, if all windows resources are busy, that's it
  my @windows_resources;
  my %w_needed;
  printf "-------------Will start %d Jobs\n", scalar(keys %found_cls);
 LOOP1:
  foreach my $cl (keys %found_cls)
  {
    foreach my $mod (keys %{$found_cls{$cl}})
    {
      if ($all_blocks{$mod}->{platforms} =~ /windows/)
      {
        $w_needed{$mod} = 1;
        foreach my $resource ($ec->Get('/resources[]'))
        {
          if ($resource->hostPlatform eq 'windows')
          {
            my $resource_name = $resource->Name;
            if ($resource->pools !~ /Arbitration_windows/)
            {
              print "Windows resource $resource_name is not in pool Arbitration_windows\n";
              next;
            }
            if ($resource->resourceDisabled)
            {
              print "Windows resource $resource_name is disabled\n";
              next;
            }

            if ($resource->stepCount)
            {
              print "Windows resource $resource_name is busy\n";
              next;
            }

            if ($dedicated_w_resource && $dedicated_w_resource ne $resource_name)
            {
              print "Windows resource $resource_name does not match requested $dedicated_w_resource\n";
              next;
            }

            push(@windows_resources, $resource);
          }
        }
        last LOOP1;
      }
    }
  }

  my $windows_resource;
  if (%w_needed)
  {
    if (!@windows_resources)
    {
      print "No windows resources available, exiting\n";
      exit 1;
    } else
    {
      # get the windows resource tha was not used recently ??
      ($windows_resource) = sort {$a->lastRunTime cmp $b->lastRunTime} @windows_resources;
    }
  }

  # Get last good cl
  if (!$last_good_cl_value)
  {
    my $cmd = "p4 changes -s submitted -m1 //sgpu/@{[$options->branchName]}/...";
    $last_good_cl_value = `$cmd`;
    if ($?)
    {
      print STDERR $last_good_cl_value;
      exit 1;
    }

    $last_good_cl_value = (split(' ', $last_good_cl_value, 3))[1];
  }

  # Create job steps to sync APL and continue
  my @cls2sync = map {split(':', $_)} keys %found_cls;
  my $command = sync_client_command(apl => 'linux', 1, $apl_changed ? \@cls2sync : ());
  $command =~ s/\$\$/\$/sg;   # Get rid of $$

  # Make sure we have windows resources available (if needed)

  my $step_name = "SyncAPL_linux";
  my $resource = get_resource('linux');
  if ($commander)
  {
    $this_job_obj->commander->abortOnError(1); # Catch errors
    $this_job_obj->commander->createJobStep(
                                            {
                                             jobStepName => $step_name,
                                             command => $command, shell => '/bin/bash -l', resourceName => $resource, parallel => 1,
                                             errorHandling => 'abortProcedure',
                                            });
    die $this_job_obj->err if $this_job_obj->err;
  } else
  {
    print "Would create job step $step_name, command <$command>\n resource $resource\n";
  }

  my $w_resource_name;
  if (%w_needed)
  {
    $w_resource_name = $windows_resource->resourceName;
    my $step_name = "SyncAPL_windows_$w_resource_name";
    my $command = sync_client_command(apl => 'windows', 1, $apl_changed ? \@cls2sync : ());
    $command =~ s/\$\$/\$/sg;   # Get rid of $$
    if ($commander)
    {
      $this_job_obj->commander->createJobStep(
                            {
                             jobStepName => $step_name,
                             command => $command, shell => 'C:\cygwin64\bin\bash --login', resourceName => $w_resource_name, parallel => 1,
                             errorHandling => 'abortProcedure',
                            });
      die $this_job_obj->err if $this_job_obj->err;
    } else
    {
      print "Would create job step $step_name, command <$command>\nresource <$w_resource_name>\n";
    }
  }

  my $index = 1;
  my $step_code_header = "#!$^X
eval 'set -x;
     perl=$^X
     Steps2Debug=\"$ENV{Steps2Debug}\"
" . <<'EOF';
pswitch="$[/javascript (myJob.PerlSwitch)]"
api_path=$api_path
if [ -n "$api_path" ] ; then
   pswitch="$pswitch $api_path"
fi
export RemoteDebugAddress=$[/javascript (myJob.RemoteDebugAddress)]
if [ "$Steps2Debug" != "" -a "$RemoteDebugAddress" != "" ] ; then
EOF
$step_code_header .= 'step_name="$' . '[/myJobStep/stepName]"
';
$step_code_header .= <<'EOF';
  export Steps2Debug
  for step in $Steps2Debug ;  do
     if [ "$step_name" = "$step" ] ; then
       PERLDB_OPTS="RemotePort=$RemoteDebugAddress"
         export PERLDB_OPTS
       PERL5LIB="$[/javascript getProperty ("/projects[$[/myJob/projectName]]/PerlDebLib")]"
         export PERL5LIB 
       pdeb="-d"
         echo "Running perl in debug mode"
       break 
  fi 
done
fi 
pdeb="$pdeb "

exec $perl $pdeb $pswitch -S $0 ${1+"$@"}'
  if 0;

use strict;
use Ecloud::Ec;

# This is a nuisance
$ENV{PERL_LWP_SSL_VERIFY_HOSTNAME} = 0;
delete $ENV{COMMANDER_HTTP_PROXY};

my $ec = Ecloud::Ec->new_with_options;

die $ec->err if $ec->err;

EOF

  my $step_code = $step_code_header;
  my $commander_host = $ec->host;

  my $ind;
  foreach my $orig_key (keys %found_cls)
  {
    # Sort
    my $key = join(':', sort {$cl_ind{$a} <=> $cl_ind{$b}} split(':', $orig_key));
    my $w_needed = grep {exists $w_needed{$_}} keys %{$found_cls{$orig_key}};
    my $mods = join(':', keys %{$found_cls{$orig_key}});
    print "Found $key:$mods\n";

    $ind++;
    my $mkf_name = "ci_${this_job_id}_$ind.mak";

    my $mkf_val = "$scriptdir/Makefile.gen SKIP_APL=1 MODULES=$key:$mods CLIENTINDEX=$index LAST_GOOD_CL=$last_good_cl_value MAK_NAME=$mkf_name" . ($build_user ? " BUILD_USER=$build_user" : '');
    $step_code .= <<"EOF";

    my \@params = (
                  {actualParameterName => 'Makefile', value => q!$mkf_val!},
                  {actualParameterName => 'branchName', value => '@{[$options->branchName]}'},
                 );
EOF
    # Add debugging
    foreach my $p (qw/RemoteDebugAddress Steps2Debug/)
    {
        $step_code .= <<"EOF";
        if (\$ENV{$p})
        {
        push(\@params, {actualParameterName => '$p', value => '$ENV{$p}'});
        }
EOF
    }

    # Add windows resource
    if ($w_needed)
    {
      $step_code .= <<"EOF";
        push(\@params, {actualParameterName => '$windows_resource_prop', value => '$w_resource_name'});
EOF
    }

    # Start a job
      $step_code .= <<"EOF";
      my \$job_id = \$ec->runProcedure("$project_name", 
                                     {
                                      procedureName => "$genmake_name", 
                                      actualParameter => \\\@params,
                                     }
                                    );
EOF
    my $link = sprintf(" CL: %s, modules: %s", join(' ', split(':', $key)), join(' ', split(':', $mods)));
      $step_code .= <<"EOF";
      die \$ec->err if \$ec->err;

      print "Started \$job_id\n";
    
      # Set modules in progress
      \$ec->Create("$running_jobs_prop/properties[\$job_id]", {value => "$mods"});
      die \$ec->err if \$ec->err;
    #Create URL
      \$ec->Create('/myJob/properties[report-urls]/properties[$link]', {value => "http://$commander_host/commander/jobDetails.php?jobId=\$job_id"});
      die \$ec->err if \$ec->err;
EOF
      $index++;
  }

  # Create final
  if ($commander)
  {
    $this_job_obj->commander->createJobStep(
                                            {jobStepName => 'dispatch',
                                            command => $step_code}
                                           );
    die $this_job_obj->err if $this_job_obj->err;
  } else
  {
    print "Would create the final step <$step_code>\n";
  }
}

sub add_postp {
  my ($cp) = @_;

  # Wrap, add echo and add postp
  # Process command and find start of shell
  my @new_c;
  my $start;
  foreach my $str (split("\n", $$cp))
  {
    if (!$start && index($str, 'GENMAKE_') == -1)
    {
      $start++;
      push(@new_c, "\t(");
    }

    push(@new_c, $str);
  }

  push(@new_c, split("\n", '	)
	status=$$?
	if [ $$status -ne 0 ] ; then
	  echo FAILED
	else
	  echo PASSED
	fi
	exit $$status
'));

  $$cp = join("\n", @new_c);

  # Add postp
  $$cp = "GENMAKE_postProcessor='$postp'
\t$$cp";
}

sub get_cleanup_target {
  my ($platform) = @_;

  "clean.$platform";
}

sub add_cleanup_target {
  my ($goal, $platform) = @_;

  my $cleanup_target = get_cleanup_target($platform) . ".$goal";
  _add_edge($graph, $top, $cleanup_target);
  _add_edge($graph, $cleanup_target, 'cleanup');
  _add_edge($graph, $top, 'cleanup');

  my $client_root = get_client_root($goal, $platform);
  my $resource = get_resource($platform);

  my $shell = $platform eq 'linux' ? '/bin/bash -l' : $cygwin_shell;
    # Command
    my $command = qq&GENMAKE_GROUP=$platform,$goal
\tGENMAKE_shell='$shell'
\tGENMAKE_stepName=clean_client
\tGENMAKE_releaseExclusive=1
\tGENMAKE_resourceName=$resource
\tGENMAKE_alwaysRun=1
\trm -rf $client_root/*&;

  $graph->set_vertex_attribute($cleanup_target, command => $command)
}

sub check_group {
  my ($hash, $target, $command) = @_;

  my ($group) = $command =~ /GENMAKE_GROUP=(.*?)\n/s;
  my ($step_name) = $command =~ /GENMAKE_stepName=(.*?)\n/s;

  if (exists $hash->{$group}{$step_name})
  {
    die "Internal error, $target: $step_name already exists in group $group\n";
  } else
  {
    $hash->{$group}{$step_name} = ();
#    print "$target: $step_name added to group $group\n";
  }

}

sub set_eval_target 
{
  my ($target, $graph_list, $group, $cl_set, $comb_property) = @_;

  _add_vertex($graph, $target);

  # Top depends on it
  _add_edge($graph, $target, $top);

  # Add edges
  foreach my $g (@$graph_list)
  {
    foreach my $p ($g->successorless_vertices)
    {
      _add_edge($graph, $p, $target);
    }
  }

  # Set command
  my @prereqs = $graph->predecessors($target);

  my $level = 0;

  $level = (split('_', $comb_property))[-1] if $comb_property;

  my $condition = "setProperty('/myJobStep/clOrder', '@cl_order');setProperty('/myJobStep/combinationIndex', $level);setProperty('/myJobStep/prerequisites', '@prereqs');setProperty('/myJobStep/ClSets', '$cl_set')";

  $condition .= ";var result;if (getProperty ('$comb_property')){result = true} else {result = false;}result" if $comb_property;

  my $resource = get_resource('linux');
  my $command = qq&GENMAKE_GROUP=$group
\tGENMAKE_resourceName=$resource
\tGENMAKE_condition="$condition"
\tGENMAKE_alwaysRun=1
\tGENMAKE_stepName=EvaluateResult
\tGENMAKE_commandFile=$eval_target_file
&;
  check_group(\%group_hash, $target, $command);
  $graph->set_vertex_attribute($target, command => $command);
  1;
}

# To test arbitration:
#/home/apps/perl_org/perl-5_12_3/bin/perl -d /mntdir/proj/escher/A0/workareas/y.shtil/ec_work/apl/cad/build_scripts_dev/ini2make2.pl --host ec-s-stg.sisa.samsung.com --project NewApl --procedure genmake-debug --top CI --in ci.ini --arbitrate --scriptdir /mntdir/proj/escher/A0/workareas/y.shtil/ec_work/apl/cad/build_scripts_dev


# After arbitration:
# /home/apps/perl_org/perl-5_12_3/bin/perl -d /mntdir/proj/escher/A0/workareas/y.shtil/ec_work/apl/cad/build_scripts_dev/ini2make2.pl --host ec-s-stg.sisa.samsung.com --project NewApl --modules 195148:gfxbench30:eglretrace:cbcl12-mobile:castor:compiler:ocl:ets:PPA:fs:apitrace:driver:compiler_test  --last_good_cl 195151 --top CI --in ci.ini --procedure genmake-debug --job 123 --noarbitrate --output foo.mak
__END__

