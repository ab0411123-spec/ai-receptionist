CREATE TABLE login (
    user VARCHAR(50),
    password VARCHAR(50)
);
<?php
$conn = mysqli_connect("localhost", "root", "", "test");

$username = "ammu";
$password = "1234";

$sql = "INSERT INTO login (user, password) VALUES ('$username', '$password')";

if (mysqli_query($conn, $sql)) {
    echo "Data inserted successfully";
} else {
    echo "Error";
}
?>