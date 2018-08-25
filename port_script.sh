FILE=backwpup_dc661a_2018-08-20_03-27-12.tar.gz
REMOTE_PATH=/customers/d/5/0/skindeepmag.com/httpd.www/wp-content/uploads/backwpup-dc661a-backups
BACKUP_DIR=backup
SQL_FILE=skindeepmag_com.sql.gz
CONTAINER_NAME=mariadb
DB_PASSWORD=password
# Abort at first error
set -e
# Print commands (with expanded vars)
set -x
# Download backup
# sftp skindeepmag.com@ssh.skindeepmag.com:"$FILE/$REMOTE_PATH"
# Extract backup
# mkdir $BACKUP_DIR
# tar -xzf $FILE --directory $BACKUP_DIR/
# Start a new mariaDb instance
docker run --rm -p 127.0.0.1:3306:3306 --name $CONTAINER_NAME -e MYSQL_ROOT_PASSWORD=$DB_PASSWORD -d mariadb:latest
# Copy the instructions into the container
docker cp $BACKUP_DIR/$SQL_FILE $CONTAINER_NAME:/
docker cp porting $CONTAINER_NAME:/porting
# Create a target database
sleep 10
docker exec mariadb mysql -u root --password=$DB_PASSWORD -e "CREATE DATABASE wp;"
# Load the database instructions into the database
docker exec -i mariadb sh -c 'zcat skindeepmag_com.sql.gz | mysql -u root --password=password wp'
