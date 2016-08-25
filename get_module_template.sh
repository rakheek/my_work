#!/bin/bash

usage() 
{
    echo "ERROR:Usage: $0 -m MODULE [-c - create from existing if available] [-b BRANCH default main]" ;exit 1
}

branch=main
while getopts "b:m:c" o;do
    case "${o}" in
        m)
            m=${OPTARG}
            ;;
        b)
            branch=${OPTARG}
            ;;
        c)
            create=1
            ;;
        *)
            usage
            ;;
        esac
done
shift $((OPTIND-1))

if [ $# -ne 0 -o -z "$m" ] ; then
    usage
fi

rtl_builds="rtl_build rtl_build_svport tb_build vcs_build tb_build_gpu111"

test_builds="gfxbench30 PPA eglretrace cbcl12-mobile compiler_test"

list="apl compiler driver fs ocl ets castor cachesim ts apitrace models_core dvm $rtl_builds $test_builds"
#echo Testing agaist $list
for n in $list ; do
    if [ "$n" = "$m" ] ; then
        found=$n
        break
    fi
done

if [ -z "$found" ] ; then
    echo ERROR $m does not match any of \'$list\' 2>&1
    exit 1;

fi

for mm in $rtl_builds ; do
    if [ "$mm" = "$m" ] ; then 
        f=1
        m=rtl
        break
    fi
done

if [ -z "$f" ] ; then
    for mm in $test_builds ; do
        if [ "$mm" = "$m" ] ; then 
            m=smoke
            break
        fi
    done
fi

# map rtl to rtl

t="ec_sgpu_${branch}-${m}_template"
t1="ec_sgpu_${branch}-${m}"

p4=/home/escher-de/bin/prod/p4

res="`$p4 client -o -t $t bla 2>&1`"

if [ $? -ne 0 ]; then
    echo "$res" 2>&1
    echo ERROR Client template $t for module $found is bad 2>&1
    # Try without template

    $p4 client -o -t $t1 bla 1>/dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo ERROR Client template $t1 for module $found is bad AS WELL 2>&1
        exit 1
    else
        if [ -n "$create" ] ; then
            echo Will create $t from $t1
            $p4 client -o -t $t1 $t | sed -r -e 's/^Host:.*//' -e 's@^Root:.*@Root:	/dev/null@' | $p4 client -i
        else
            exit 1;
        fi
    fi
fi

echo $t

