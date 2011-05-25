#!/usr/bin/perl -w
# $Id$
# $HeadURL$

use Data::Dumper;
use MIME::Base64;
use LWP::Simple;
use HTTP::Request::Common qw(POST);
use LWP::UserAgent;
use Getopt::Long;
use Term::ANSIColor;

my $PROG = 'avatar';
my $opt_namespace;
my $opt_verbose;
my $opt_file;
my $opt_cust = "";
my %spec_cust;

sub usage {
    print STDERR <<EOF
Avatar - Avatar Fetcher, Taobao Inc.
Usage:
    $PROG [options]
Options:
    -h/--help				Help
    -v/--verbose			Run commands in verbose mode
    -c/--cust				divsion customer packages
    -n/--namespace			use specified namespace
    -s/--save				save avatar to <namespace>.avatar
    -f/--file				use exist avatar file instead fetch snap

EOF
    ;
    exit(1);
}

#MESSAGE control sub functions
sub debug {
    my ($text) = @_;
    print colored(["bold", "dark" ,""],"DEBUG:");
    print $text."\n";
}

sub info {
    my ($text) = @_;
    print colored(["bold", "white" ,""],"INFO:");
    print $text."\n";
}

sub success {
    my ($text) = @_;
    print colored(["bold", "green" ,""],"MESSAGE:");
    print $text."\n";
}
sub warning {
    my ($text) = @_;
    print colored(["bold", "yellow" ,""],"WARNING:");
    print $text."\n";
}

sub error {
    my ($text) = @_;
    print colored(["bold", "red" ,""],"ERROR:");
    print $text."\n";
}

# Simple Email Function
# ($to, $from, $subject, $message)
sub sendEmail
{
my ($to, $from, $subject, $message) = @_;
my $sendmail = '/usr/lib/sendmail';
open(MAIL, "|$sendmail -oi -t");
print MAIL "From: $from\n";
print MAIL "To: $to\n";
print MAIL "Subject: $subject\n\n";
print MAIL "$message\n";
close(MAIL);
}
 
sub getRPM_URL {
	($p,$name,$version,$arch,$release) = @_;
	$p = $name."-".$version."-".$release.".".$arch.".rpm";
	$rhel = `rpm -q redhat-release --qf "%{v}"`;
	if ( -e "/usr/bin/curl" ){
		$opt_verbose && debug("curl -s 'http://package.server.taobao.com/cgi-bin/rpmfind?name=$p&rhel=$rhel");
		$res = `curl -s 'http://package.server.taobao.com/cgi-bin/rpmfind?name=$p&rhel=$rhel'`;
	}elsif ( -e "/usr/bin/wget" ){
		$res = `wget -q 'http://package.server.taobao.com/cgi-bin/rpmfind?name=$p&rhel=$rhel' -O /dev/stdout`;
	}else{
		error "Neither curl or wget on this host, can not location rpm package, please install one. program exit";
		exit 1;
	}
	if ($res) {
		return $res;
	}

}

sub postAvatar {
  my $ua = LWP::UserAgent->new;
  $ua->agent("Avatar/0.1");

  # Create a request
  my $req = HTTP::Request->new(POST => 'http://avatar.tbsite.net:9999/PostAvatar.php');
  $req->content_type('application/x-www-form-urlencoded');
  $req->authorization_basic( $username, $password );
  $req->content("@_");
  # Pass request to the user agent and get a response back
  my $res = $ua->request($req);
  # Check the outcome of the response
  if ($res->is_success) {
	if($res->content =~ /^OK$/){
	      success("Avatar commited successfuly");
	}else{
		error($res->content);
	}
  }
  else {
       error($res->status_line);
  }
}


GetOptions(
	"verbose|v" => \$opt_verbose,
	"namespace|n=s" => \$opt_namespace,
	"file|f=s" => \$opt_file,
	"cust|c=s" => \$opt_cust,
	"save|s" => \$opt_save,
	"help|h" => \$opt_help
);

$opt_help && &usage();
#@ARGV || &usage();

my $tmpdir = '/tmp/.avatar';
`rm -fr $tmpdir && mkdir $tmpdir`;
if ( $opt_namespace ){
	$namespace = $opt_namespace;
	$namespace .= "\n";
}else{
	my $hostname = `/bin/hostname`;
	$namespace = $hostname;
}

if ( $opt_cust ){
	%spec_cust = map {$_,""} split (/ /,$opt_cust);
}

if (! $opt_save){
	print "Enter your svn  account: ";
	chomp($username = <>);
	system("stty -echo");
	print "Enter your svn password: ";
	chomp($password = <>);
	system("stty echo");
	print "\n";
	print "Enter Avatar Commit Comment (> 5 letters): ";
	chomp($comment = <>);
	$comment =~ s/ /\ /ig;
}

if (! $opt_file ){
info("Fetching Avatar...");
my @rpm_groups = (
"Amusements/Games",
"Amusements/Graphics",
"Applications/Configuration",
"Applications/Communications",
"Applications/CPAN",
"Applications/Multimedia",
"Applications/Shells",
"Applications/Text",
"Applications/Archiving",
"Applications/Publishing",
"Applications/File",
"Applications/Internet",
"Applications/Editors",
"Applications/System",
"Applications/Emulators",
"Applications/Engineering",
"Applications",
"Applications/Databases",
"Application/System",
"Applications/Productivity",
"Documentation",
"Documentation/Man",
"Development/Compilers",
"Development/Libraries",
"Development/Tools",
"Development/System",
"Development/Debuggers",
"Development/Testing",
"Development/Framework",
"Development/Code Generators",
"Development/Languages",
"Development/Documentation",
"Development/Libraries/Java",
"Development/Java",
"Development/Build Tools",
"Development/GNOME and GTK+",
"Development/C",
"Development/Tools/Other",
"Development/Libraries/Application Frameworks",
"Desktop/Accessibility",
"Internet/WWW/Indexing/Search",
"Internet/WWW/Dynamic Content",
"IBM",
"Libraries",
"Networking/WWW",
"Networking/Daemons",
"Networking/Diagnostic",
"OpenLDAP servers and related files.",
"Public Keys",
"Productivity/Networking/Diagnostic",
"Productivity/Security",
"Security/Cryptography",
"System Environment/Kernel",
"System Environment/Base",
"System Environment/Daemons",
"System Environment/Libraries",
"System Environment/Shells",
"System Environment/Tools",
"Systems Management/Base",
"System Environment/Applications",
"System Environment/System",
"System/Logging",
"System/Console",
"System/Libraries",
"System/Boot",
"Text Editors/Integrated Development Environments (IDE)",
"Text Processing/Markup/XML",
"Utilities/System",
"Utilities",
"User Interface/X",
"User Interface/Desktops",
"User Interface/X Hardware Support"
);

my %target_rpms = map {$_, ""} split(/\n/, qx{rpm -qa --qf "%{N}-%{v}-%{r}.%{arch}\n"|grep -v gpg-pubkey|grep -v -E '^avatar'|grep -v -E '^walle'| sort});

for ( @rpm_groups ) {
	chomp;
	my %this_group = map {$_, ""} split(/\n/, qx{rpm -q -g '$_' --qf "%{N}-%{v}-%{r}.%{arch}\n" |grep -v gpg-pubkey|grep -v -E '^avatar'|grep -v -E '^walle'});
	if ( ! grep (/does not contain any packages/i, %this_group) ){
		$base_rpms{$_} = "" foreach (keys %this_group);
	}
}


$opt_cust && delete $base_rpms{$_} foreach (keys %spec_cust);

@cust_rpms = grep { !defined($base_rpms{$_}) } keys %target_rpms;


my ($sec,$min,$hour,$mday,$mon,$year,$wday,
		$yday,$isdst)=localtime(time);

$avatar  = "###################\n";
$avatar .= "#AVATAR State File#\n";
$avatar .= "###################\n";
$avatar .= "namespace=$namespace";
$avatar .= "timestamp=\"";
$avatar .= sprintf ("%4d-%02d-%02d %02d:%02d:%02d", $year+1900,$mon+1,$mday,$hour,$min,$sec );
$avatar .= "\"\nbase_rpms_num=";
$avatar .= scalar keys %base_rpms ;
$avatar .= "\n";
$avatar .= "cust_rpms_num=";
$avatar .= scalar @cust_rpms;
$avatar .= "\n";
$avatar .= "base_rpms=\"";
for ( %base_rpms ) {
	$avatar .= $_." ";
}
$avatar .= "\"\n";
$avatar .= "cust_rpms=\"";
my $diff_files = "";
for (@cust_rpms) {
	my $diff_file = "";
	my $rpm = $_;
	$avatar .= $rpm." ";
	$verify = `rpmverify $rpm --nogroup --nouser --nomtime --nomode`;
	$opt_verbose && debug("rpmverify $rpm --nogroup --nouser --nomtime --nomode");
	@lines = split("\n",$verify);
	for ( @lines ) {
	$line = $_;
	if ( $line =~ m/.*?\/(.*)/ig ){
		#print $1."\n";
		my $changed_file = $1;
		my $stage_file = "/".$changed_file;
		my $conf_files = `rpm -qc $rpm`;
		if(grep (/$changed_file/i,$conf_files)){
		my $extract_file = './'.$changed_file;
		my $rpm_file = $tmpdir."/".$changed_file;
		$p = `rpm -q $rpm`;
		$name = `rpm -q --qf %{N} $rpm`;
		$version = `rpm -q --qf %{V} $rpm`;
		$arch = `rpm -q --qf %{ARCH} $rpm`;
		$release = `rpm -q --qf %{R} $rpm`;
		$opt_verbose && debug( $p." ".$name." ".$version." ".$arch." ".$release);
		$p_url = getRPM_URL($p,$name,$version,$arch,$release);
		$p_url =~ s/\n//ig;		
		$opt_verbose && debug( $p_url );		
		if (!$p_url){
			warning "$p not exists on yum server, please check.";
		}else{
			$p_url =~ m/.*\/(.*)/;
			$ori_package = $1;
			if ( ! -e $tmpdir."/".$ori_package ){
				`cd $tmpdir; wget -q $p_url -O $tmpdir/$ori_package`;
				$opt_verbose && debug("wget -q $p_url -O $tmpdir/$ori_package");
			}else{
				$opt_verbose && debug("$ori_package exists, skip downloading...");
			}
			$opt_verbose && debug("cd $tmpdir; rpm2cpio $tmpdir/$ori_package |cpio -id $extract_file 2>/dev/null");
			`cd $tmpdir; rpm2cpio $tmpdir/$ori_package |cpio -id $extract_file 2>/dev/null`;

			
			$diff = `diff -u $rpm_file $stage_file`;
			$opt_verbose && debug("diff -u $rpm_file $stage_file");
			$encoded = encode_base64($stage_file);
			chomp($encoded);
			$diff_file = $tmpdir."/".$encoded.".diff";
			$diff_files .= $stage_file.".diff ";
			$encoded_diff_files .= $diff_file." ";
			open( FP, "> $diff_file" );
			print FP $diff;
			close FP;
			}
		}
	}
	}
}
$avatar .= "\"\n";
$avatar .= "diff_files=\"$diff_files\"\n";
if ($comment){
	$avatar .= "comment=\"$comment\"\n";
}else{
	$avatar .= "comment=\"\"\n";
}
$avatar .= "###END OF AVATAR###\n";
if ($encoded_diff_files){
	@diffs = split(/ /,$encoded_diff_files);
	for(@diffs){
		$raw_data = "";
		open(FP, $_) || die("Could not open file!");
		while ($line = <FP>){
			$raw_data .= $line;
		} 
		close FP;
		my $tmp = $_;
		$tmp =~ s/.diff$//gi;
		$tmp =~ s/$tmpdir\///g;
		my $real_diff = decode_base64($tmp);
		$avatar .= $real_diff.".diff\n".$raw_data."\n";

	}
}

}else{# read from saved avatar file
$avatar = "";
open(FP,$opt_file) || die("Could not open file!");
	while ($line = <FP>){
		if ($line !~ /^comment=/){
			$avatar .= $line;
		}else{
			$avatar .= "comment=\"$comment\"\n";
		}
	}
close FP;
}

$opt_verbose && debug($avatar);
if ($opt_save){
	info("Writing state file...");
	chomp ($namespace);
	$savefile = $namespace.".avatar";
	open ( FP, "> $savefile");
		print FP $avatar;
	close FP; 
	success("Saved as $namespace.avatar.");
}else{
	info("Commiting...");
	postAvatar("$avatar");
	print "\n";
}
`rm -fr $tmpdir`;
