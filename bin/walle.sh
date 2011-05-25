#!/bin/bash
# $HeadURL$
# $Id$

##########INITIAL###########
hostname=${HOSTNAME}
MYNAME="I am a Avatar Installer @Taobao Inc."
CONFHOST=avatar.server.taobao.com
USERTTY=`tty |sed -e 's/\/dev\///g'|sed -e 's/\//\\\\\//g'`
USER=`w|grep $USERTTY|awk '{print $1}'`
### Color Prompt###
bldblk='\e[1;30m' # Black - Bold
bldred='\e[1;31m' # Red
bldgrn='\e[1;32m' # Green
bldylw='\e[1;33m' # Yellow
bldblu='\e[1;34m' # Blue
bldpur='\e[1;35m' # Purple
bldcyn='\e[1;36m' # Cyan
bldwht='\e[1;37m' # White
txtrst='\e[0m'    # Text Reset
#############################

function main (){
	# define source file
	rm -fr /tmp/.avatar
	mkdir /tmp/.avatar
	sfile="/tmp/.avatar/"`hostname`".appconf"
	avatar_file="/tmp/.avatar/"`hostname`".avatar"
	if [ $opt_namespace ]
	then
		namespace=$opt_namespace
	else
		namespace=$hostname
	fi
	confurl="http://$CONFHOST:9999/GetAvatar.php?namespace=$namespace"
	# revision process
	if [ $revision ]
	then
		confurl=$confurl"&revision=$revision"
	fi
	walle_say "$MYNAME";
	if [ $revision ]
	then
		dis_revision="Rev "$revision
	else
		dis_revision="Last Revision"
	fi
	info "Getting Avatar for $namespace $dis_revision ...";
	if [ $verbose ]
	then 
		debug $confurl
	fi
	#add log to system
	echo `date +"%Y-%m-%d %T"`" Restore Avatar AS $namespace $dis_revision by $USER" >> /var/log/avatar.log
	#get source from appconf server
	if [ ! -z "$fromfile" ]
	then
		avatar_file=$fromfile
		sed -e "1,/###END OF AVATAR###/p" $avatar_file -n > $sfile && source $sfile;
	else
		wget -qO /dev/stdout $confurl |tee $avatar_file|sed -e "1,/###END OF AVATAR###/p" -n > $sfile && source $sfile && rm -f $sfile;
	fi
	if [ -z "$namespace" ]
	then 
		error "namespace empty";exit 1;
	fi
	if [ -z "$base_rpms" ]
	then
		error "base_rpms empty";exit 1;
	fi
	if [ -z "$cust_rpms" ]
	then
		info "cust_rpms empty, hope it is ok";
	fi
	info "Checking Host Package State ..."
	#clean previous log
	base_rpms_log="/tmp/.avatar/"$namespace"-install-base-"$revision".log"
	cust_rpms_log="/tmp/.avatar/"$namespace"-install-cust-"$revision".log"
	rpm_need_to_install_log="/tmp/.avatar/"$namespace"-need-to-install-rpms-"$revision".log"
	
	redundant_rpms_log="/tmp/.avatar/"$namespace"-redundant-rpms.log"
	rpm -qa --qf %{n}"-"%{v}"-"%{r}"."%{arch}"\n" > $redundant_rpms_log
	sed -i -e "/^gpg-pubkey/d" $redundant_rpms_log #ignore gpg-pubkey
	touch $base_rpms_log
	cat /dev/null > $base_rpms_log
	touch $cust_rpms_log
	cat /dev/null > $cust_rpms_log
	
	# judge redhat-release, if different with target host then skip_base=true
	redhat_release=`rpm -q redhat-release --qf %{n}"-"%{v}"-"%{r}"."%{arch}`
	for line in $base_rpms
	do
		if [ "$line" = "$redhat_release" ]
		then
			avatar_redhat_release=$line
			break
		fi
	done
	if [ -z $avatar_redhat_release ] || [ -z "$base_rpms" ]
	then
		warning "This Server's release version different from snapshot, auto add -k option."
		skip_base=true
	fi
	
	# Check Base Packages
	# Record exactly base RPMS needed to install
	# Remove Them from Redundant
	if [ $skip_base ]
	then
		for line in $base_rpms
		do
			sed -i -e "/^$line/d"  $redundant_rpms_log
		done
	else
		cat /dev/null > /tmp/$namespace-avatar-base.log
		for line in $base_rpms
		do
			echo $line >> /tmp/$namespace-avatar-base.log
		done
		sort /tmp/$namespace-avatar-base.log > /tmp/$namespace-avatar-base.sorted # avatar base sorted file
		
		rpm -qa --qf %{n}"-"%{v}"-"%{r}"."%{arch}"\n" |grep -v -E '^gpg-pubkey'|sort > /tmp/$namespace-rpms-all.sorted # localhost base sorted file # remove exists base from redundant
		for line in `cat /tmp/$namespace-avatar-base.sorted`
		do
			sed -i -e "/^$line/d"  $redundant_rpms_log
			####### Skip Critical RPMS #######
			rpm=`rpm -q rpm`
			glibc=`rpm -q glibc`
			openssl=`rpm -q openssl`
			sed -i -e "/^$rpm/d" /tmp/$namespace-avatar-base.sorted
			for g in $glibc
			do
				sed -i -e "/^$g/d" $redundant_rpms_log
				sed -i -e "/^$g/d" /tmp/$namespace-avatar-base.sorted
			done
			for o in $openssl
			do 
				sed -i -e "/^$o/d" $redundant_rpms_log
				sed -i -e "/^$o/d" /tmp/$namespace-avatar-base.sorted						
			done
		done
		diff /tmp/$namespace-avatar-base.sorted /tmp/$namespace-rpms-all.sorted |grep -E '^<' |awk '{print $2}' >> $base_rpms_log #need to install	
	fi # end of skip base

	# Check Custom Packages
	# Record exactly cust RPMS need to install
	# Remove Them from Redundant
	for line in $cust_rpms
	do
		trap exit 2
		#rpm -q $line --quiet
		rpm -V $line --nomtime --nouser --nogroup --nomode > /tmp/.avatar/$line.verify
		rpm -qc $line > /tmp/.avatar/$line.qc 
		grep -f /tmp/.avatar/$line.qc /tmp/.avatar/$line.verify
		if [ $? -eq 0 ]
		then
			echo $line >> $cust_rpms_log
		else
			info "CUST RPM:"$line" already exists"
			sed -i -e "/^$line$/d" $redundant_rpms_log
		fi
	# Other Version exists
	rpm_name=""
	rpm_name=${line%%.*}
	rpm_name=${rpm_name%-*}
	rpm -q $rpm_name --quiet
	if [ $? -eq 0 ]
	then
		older_rpm=`rpm -q $rpm_name --qf "%{N}-%{v}-%{r}.%{arch}\n"`
		if [ $older_rpm != $line ]
		then
			info "Found Other Version RPM:"$older_rpm
			echo $older_rpm >> $redundant_rpms_log;
		fi
	fi
	done #end of for line of cust_rpms

	#Exclude Remove walle
	walle=`rpm -q walle --qf "%{N}-%{v}-%{r}.%{arch}\n"`
	sed -i -e "/^$walle$/d" $redundant_rpms_log

	# Do a Summary Report
	summary
	if [ $check ]
	then
		exit 1
	fi

	if [ ! $skip_prompt ]
	then
		echo -n "Let Wall-E Perform This Action(yes)? "
		while read Action; do
		if [ ! $Action = "yes" ]
		then
			exit 1
		fi
		break
		done
	fi

	info "Removing  Redundant Packages ..."
	# Process Redundant Packages First
	while [ -s $redundant_rpms_log ]
	do
		for p in `cat $redundant_rpms_log`
		do
			trap exit 2
			if [ $verbose ]
			then
				debug "rpm -ev $p --nodeps"
			fi
			rpm -ev $p --nodeps
			if [ $? -eq 0 ]
			then
			sed -i -e "/^$p$/d" $redundant_rpms_log
			fi
		# Remove rpm files
		if [ ! "$save_rpmfiles" ]
		then
			conf_files=""
			conf_files=`rpm -qlc $p`
			for cf in $conf_files
			do
				rm -f $cf".rpmsave" $cf".rpmnew" $cf".rpmorig"
			done # end of for cf
		fi # end of if save_rpmfiles
		done # end of for p
	done # end of while

	info "Merge Base Packages and Cust Packages ..."

	cat $base_rpms_log > $rpm_need_to_install_log
	cat $cust_rpms_log >> $rpm_need_to_install_log

	info "Installing All RPM Packages Needed to Install ..."
	if [ -s $rpm_need_to_install_log ]
	then
		for p in `cat $rpm_need_to_install_log`
		do
			trap exit 2
			rpm_location=""
			locate_rpm_url $p
			info "rpm -ivh $rpm_location"
			if [ ! -z "$rpm_location" ]
			then
				all_location=$all_location" "$rpm_location
			fi
		done
	fi
	rpm -ivh $all_location

	for p in `cat $rpm_need_to_install_log`
	do
		rpm -q $p
		if [ $? -eq 0 ]
		then
			sed -i -e "/^$p$/d" $rpm_need_to_install_log
			# Remove rpm files
			if [ ! "$save_rpmfiles" ]
			then
				conf_files=""
				conf_files=`rpm -qlc $p`
				for cf in $conf_files
				do
					rm -f $cf".rpmsave" $cf".rpmnew" $cf".rpmorig"
				done # end of for cf
			fi # end of if save_rpmfiles
		fi # end of if rpm -q $p
	done # end of for p

	if [ -s $rpm_need_to_install_log ]
	then
		error "Following Packages not install, please check or run again"
		cat $rpm_need_to_install_log
		exit 1
	fi
	info "Patching Changed Files ..."
	if [ "$opt_dontpatch" ]
	then
		for n in $opt_dontpatch
		do
			echo $n >> /tmp/.avatar/$namespace.dontpatch
		done
		for n in $diff_files
		do
			echo $n >> /tmp/.avatar/$namespace.needpatch
		done
		grep -v -f /tmp/.avatar/$namespace.dontpatch /tmp/.avatar/$namespace.needpatch
		diff_files=`grep -v -f /tmp/.avatar/$namespace.dontpatch /tmp/.avatar/$namespace.needpatch`
	fi

	debug "Final Patch diff files:"$diff_files
	diff_array=(`echo $diff_files`)
	count=${#diff_array[@]}
	info "Parsing Avatar $count config files need to patch..."
	# Process Patch Files
	i=0
	for line in $diff_files
	do
		trap exit 2
		conf_file=${line%%.diff}
		diff_file="/tmp/.avatar/"`echo -n $conf_file|openssl base64|sed -e 'N;s/\n//g'`".diff"
		next_i=$(( $i + 1 ))
		if [ ! $next_i -eq $count ]
		then
			this_line=`grep -n -E $line'$' $avatar_file|awk -F : '{print $1}'`
			next_line=`grep -n -E ${diff_array[$next_i]}'$' $avatar_file|awk -F : '{print $1}'`
			#echo $this_line
			#echo $next_line
			num=`grep -n -E $line'$' $avatar_file|wc -l`
			if [ "$num" -ge 2 ]
			then
				error "One more diff files found, please check avatar file"
				exit 1
			fi
			num=`grep -n -E ${diff_array[$next_i]}'$' $avatar_file|wc -l`
			if [ "$num" -ge 2 ]
			then
				error "One more diff files found, please check avatar file"
				exit 1
			fi
			this_line=$(( $this_line + 1 ));
			next_line=$(( $next_line - 1 ));
			sed -n ${this_line},${next_line}p $avatar_file > $diff_file
			echo "" >> $diff_file
		else
			this_line=`grep -n -E $line'$' $avatar_file|awk -F : '{print $1}'`
			#echo $this_line
			this_line=$(( $this_line + 1 ));
			sed -n ${this_line}',$p' $avatar_file > $diff_file
			echo "" >> $diff_file
		fi
		if [ $verbose ]
		then
			debug $conf_file" "$diff_file
		fi
		if [ $answer_no_to_patch ]
		then
			patch_args=" -t"
		fi
		owner=`/bin/ls -lG $conf_file|awk '{print $3}'`
		group=`/bin/ls -lg $conf_file|awk '{print $3}'`
		sudo -u $owner patch $patch_args $conf_file $diff_file
		chgrp $group $conf_file
		rm -f $conf_file".rej"
		rm -f $conf_file".orig"
		let i++ 
	done #end of for diff_files
	success "Avatar Perform Finished"
} #end of main process


function detect_colo () {
	if [[ ${HOSTNAME} =~ "alimama.com$" ]]
	then
		hostname=${HOSTNAME%%.alimama.com}
		colo=${hostname##*.}
	else
		colo=${HOSTNAME##*.}".tbsite.net"
	fi
	if [[ "$colo" =~ "cm2.tbsite.net$" ]]
	then
		colo="corp"
	fi
	if [[ "$colo" =~ "cn[1-9]+.tbsite.net$" ]]
	then
		colo="corp"
	fi
	$verbose && debug "Current colo is: "$colo
	if [ -z "$colo" ]; then
		$verbose && debug "Can not determine coloname, use default package.server.taobao.com."
		colo='corp'
	fi
	if [ "$colo" = "corp" ]; then
		YUMHOST="package.server.taobao.com"
	fi
	if [ -z "$YUMHOST" ]; then
		YUMHOST="http://server.$colo"
	else
        YUMHOST="http://$YUMHOST"
	fi
	$verbose && debug "Use YUM Server: $YUMHOST."
}

function version () {
	VER='$HeadURL$'
	walle_say "$MYNAME"
	echo $VER
	echo "Visit http://http://code.google.com/p/taobao-avatar/ for more infomation"
        printf "
---Taobao Packages---
------======\\ \\------
-----(O)(O)=--,,-----
--Wall-E-__!!__//-----
-..\\ \\|___|,,,|)-----
-----/=//=/O.o\------
------\"\"\"\"\"\"\"\"\"------
---Avatar Installer--\n\n
"
	exit 1
}

function usage() {
	walle_say "$MYNAME"
	echo "Usage:"
	echo "    `basename $0` [-n] [-r] ..[options]
"
	echo "        -n		use namespace"
	echo "        -r		use revision"
	echo "        -k		skip base rpm check."
	echo "        -N		don't patch specified diff files"
	echo "        -t		Ask no questions to patch command; skip bad-Prereq patches; assume reversed"
	echo "        -f		use local avatar file."
	echo "        -c		print summary report only, not perform install."
	echo "        -y		skip perform confirm prompt."
	echo "        -z		keep rpm generate files: rpmsave, rpmnew, rpmorig."	
	echo "        -H		show Wall-E performed history."
	echo "        -h		print this help message."
	echo "        -v		verbose output."
	echo "        -V		print version."
	exit 1
}

function History () {
	tail -n 15 /var/log/avatar.log
	exit 1
}

function summary() {
	walle_say  "<<Begin of Wall-E Report>>"
	printf "###\t\tAVATAR SUMMARY\t\t\t###\n"
	printf "# NAMESPACE:\t\t"$namespace"\t\t###\n"
	printf "# TIMESTAMP:\t\t"
	echo -n "$timestamp"
	printf "\t###\n"
	printf "# REVISION:\t\t\t"
	echo -n "$dis_revision"
	printf "\t###\n"
	printf "# BASE RPM NUMBER:\t\t"$base_rpms_num"\t\t###\n"
	printf "# CUST RPM NUMBER:\t\t"$cust_rpms_num"\t\t###\n"
	warning "# BASE RPMS NEED TO INSTALL:"
	cat $base_rpms_log
	echo ""
	warning "# CUST RPMS NEED TO INSTALL:"
	cat $cust_rpms_log
	echo ""
	warning "# RPMS NEED TO REMOVE:"
	cat $redundant_rpms_log
	printf "###\t\tAVATAR SUMMARY\t\t\t###\n"
	walle_say  "<<End Of Wall-E Report>>"
}

function locate_rpm_url(){
	name=$1
	rhel=`rpm -q redhat-release --qf "%{v}"`
	if [ $verbose ]
	then
		debug "http://package.server.taobao.com/cgi-bin/rpmfind?name="$name".rpm&rhel="$rhel;
	fi
	if [ -f "/usr/bin/curl" ]
	then
		rpm_location=`curl -s 'http://package.server.taobao.com/cgi-bin/rpmfind?name='$name'.rpm&rhel='$rhel`
	elif [ -f "/usr/bin/wget" ]
	then
		rpm_location=`wget 'http://package.server.taobao.com/cgi-bin/rpmfind?name='$name'.rpm&rhel='$rhel -O /dev/stdout`
	else
		error "Neither curl or wget exists, can not location rpm package, please install one of them first."
		exit
	fi
	rpm_location=`echo $rpm_location | sed -e 's#http://package.server.taobao.com#'$YUMHOST'#g'`
	if [ ! -n "$rpm_location" ]
	then
		error $name" can not find in Yum Server.";
	fi
}

function success (){
	echo -n -e "${bldgrn}MESSAGE:"
	echo -n -e "${txtrst}"
	echo $1
}
function info (){
	echo -n -e "${bldwht}INFO:"
	echo -n -e "${txtrst}"
	echo $1
}
function warning (){
	echo -n -e "${bldylw}WARNING:"
	echo -n -e "${txtrst}"
	echo $1
}
function error (){
	echo -n -e "${bldred}ERROR:"
	echo -n -e "${txtrst}"
	echo $1
}
function debug (){
	echo -n -e "${bldcyn}DEBUG:"
	echo -n -e "${txtrst}"
	echo $1
}
function walle_say (){
	echo -n -e "${bldcyn}Wall-E:"
	echo $1
	echo -n -e "${txtrst}"
}


# script start

while getopts vr:chVkf:n:N:yHtz OPTION
do
case $OPTION in
k)
    skip_base=true
    ;;
t)
    answer_no_to_patch=true
    ;;
n)
	opt_namespace=$OPTARG
	;;
r)
	revision=$OPTARG
	;;
v)
	verbose=true
	;;
c)
	check=true
	;;
N)
	opt_dontpatch=$OPTARG
	;;
y)
    skip_prompt=true
    ;;
f)
	fromfile=$OPTARG
	;;
H)
	History	
	;;
h)
	usage
	;;
V)
	version
	;;
z)
    save_rpmfiles=true
    ;;	
\?)
	usage
	;;
esac
done

detect_colo
main
#clean up
rm -fr /tmp/.avatar
