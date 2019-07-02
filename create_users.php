<?php
/*
 * mybb_csv_users.php -- MyBB mass import users from CSV, v1.0
 *
 * (c) 2017 David King
 *
 * Licence: GPL 2.1.  No warranties express or implied.  Use at your own risk.
 *
 * This is a **COMMAND-LINE** tool for mass creation of MyBB users.
 *
 * Instructions for use:
 *      - create a csv file describing the users to create:
 *              - **DO NOT** put this anywhere in your web docroot!
 *              - The first line must be a header labelling each field
 *              - Mandatory fields: username, password, email, usergroup
 *                      - password is plain-text (hence warning about docroot)
 *              - Optional field: regdate, a unix timestamp
 *              - leading and trailing whitespace is stripped which may have
 *                implications for the password.
 *
 *      - put this code in your MyBB root directory
 *
 *      - from the shell:
 *              php mybb_csv_users.php /path/to/user_data.csv
 *
 * Errors will be printed and the script will continue with the next row,
 * so you might want to capture the output so you can rerun with those users
 * fixed.
 *
 * If everything went well, there will be no output.
 */

// Sanity/security checks
array_key_exists( 'SHELL', $_SERVER ) || die( "This tool can only be run from the command line." );
count( $argv ) == 2 || die( "syntax: ${argv[0]} <csv_file>\n" );

$csv_file = $argv[1];

define('IN_MYBB', 1);
require_once './global.php';
require_once MYBB_ROOT.'inc/datahandlers/user.php';

// Open CSV file and get header
$csv = fopen( $csv_file, 'rt' );
$hdr = array_map( 'trim', fgetcsv( $csv ) );

// Check that required fields are present
foreach( Array( 'username', 'password', 'email', 'usergroup' ) as $k ) {
        in_array( $k, $hdr ) || die( "CSV must contain $k field\n" );
}

// Read and add users
$rc = 0;
while( $u = fgetcsv( $csv ) ) {
        $u = array_combine( $hdr, array_map( 'trim', $u ) );

        // Determine group ID (yeah, this should be cached, but KISS)
        $gid = $db->simple_select( "usergroups", "gid", "title = '${u['usergroup']}'", array('order_by' => 'gid') );
        $gid = $db->fetch_field( $gid, 'gid' );
        if( !$gid ) {
                print "${u['username']}: no such group\n";
                $rc = 1;
                continue;
        }
        $u['usergroup'] = $gid;

        // Create user
        $new_user = new UserDataHandler( 'insert' );
        $new_user->set_data( $u );
        if( $new_user->validate_user() ) {
                $user_info = $new_user->insert_user();
        } else {
                foreach( $new_user->get_friendly_errors() as $err ) {
                        print "${u['username']}: $err\n";
                }
                $rc = 1;
        }
}

exit( $rc );
