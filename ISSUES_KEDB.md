### Network issue (Internet not reachable)
ping google is not working

Solution - echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
