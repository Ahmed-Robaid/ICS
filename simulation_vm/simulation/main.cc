#include <string>
#include <iostream>
#include <sstream>
#include <stdlib.h>
#include <sys/types.h> 
#include <arpa/inet.h>    
#include <sys/socket.h> 
#include <netinet/in.h> 
#include <pthread.h>
#include <jsoncpp/json/json.h>
#include "TE_process.h"

#define PORT 55555
#define TRUE 1

TE *my_te;
Json::Value inputs;
Json::Value outputs;
pthread_mutex_t simulation_lock;
unsigned int process_rate = 100000;

void* simulation(void *ptr) {
    while (1) {
        pthread_mutex_lock(&simulation_lock);
        my_te->update(inputs);
        outputs = my_te->get_state_json();
        my_te->print_outputs();
        pthread_mutex_unlock(&simulation_lock);       
        usleep(process_rate);
    }
}

std::string read_json_message(int socket_fd) {
    char buffer[1024];
    std::string data;
    int valread;
    
    // Read the full message
    while ((valread = recv(socket_fd, buffer, sizeof(buffer), 0)) > 0) {
        data.append(buffer, valread);
        // Break if we assume we've read the full message
        if (data.find("}") != std::string::npos) break;  // assumes JSON ends with "}"
    }
    return data;
}

int main(void) {
    Json::Reader reader;
    Json::FastWriter writer;
    Json::Value command;
    pthread_t process_thread;
    
    int opt = TRUE;  
    int master_socket, addrlen, new_socket, client_socket[30], max_clients = 30, activity, i, sd;
    int max_sd;  
    struct sockaddr_in address;  
    fd_set readfds;  
    
    // Initialize TE process
    my_te = new TE();
    my_te->update(inputs);

    for (i = 0; i < max_clients; i++) {  
        client_socket[i] = 0;  
    }
    
    // Create a master socket
    if ((master_socket = socket(AF_INET, SOCK_STREAM, 0)) == 0) {  
        std::cerr << "Socket creation failed" << std::endl;
        exit(EXIT_FAILURE);  
    }
    
    // Configure socket settings
    if (setsockopt(master_socket, SOL_SOCKET, SO_REUSEADDR, (char *)&opt, sizeof(opt)) < 0) {
        std::cerr << "setsockopt failed" << std::endl;
        exit(EXIT_FAILURE);  
    }
    
    // Bind the socket
    address.sin_family = AF_INET;  
    address.sin_addr.s_addr = INADDR_ANY;  
    address.sin_port = htons(PORT);  
    
    if (bind(master_socket, (struct sockaddr *)&address, sizeof(address)) < 0) {  
        std::cerr << "Bind failed" << std::endl;
        exit(EXIT_FAILURE);  
    }
    
    // Listen on the socket
    if (listen(master_socket, 3) < 0) {
        std::cerr << "Listen failed" << std::endl;
        exit(EXIT_FAILURE);
    }
    
    addrlen = sizeof(address);
    std::cout << "Waiting for connections..." << std::endl;

    while (TRUE) {  
        FD_ZERO(&readfds);  
        FD_SET(master_socket, &readfds);  
        max_sd = master_socket;
        
        // Add clients to set
        for (i = 0; i < max_clients; i++) {  
            sd = client_socket[i];  
            if (sd > 0) FD_SET(sd, &readfds);  
            if (sd > max_sd) max_sd = sd;  
        }
        
        // Wait for activity
        activity = select(max_sd + 1, &readfds, NULL, NULL, NULL);
        if (activity < 0 && errno != EINTR) {
            std::cerr << "Select error" << std::endl;
        }
        
        // Incoming connection
        if (FD_ISSET(master_socket, &readfds)) {
            if ((new_socket = accept(master_socket, (struct sockaddr *)&address, (socklen_t*)&addrlen)) < 0) {
                std::cerr << "Accept failed" << std::endl;
                exit(EXIT_FAILURE);
            }
            std::cout << "New connection established" << std::endl;
            
            // Add new socket to array
            for (i = 0; i < max_clients; i++) {
                if (client_socket[i] == 0) {
                    client_socket[i] = new_socket;
                    break;
                }
            }
        }
        
        // IO operation on a client socket
        for (i = 0; i < max_clients; i++) {
            sd = client_socket[i];
            if (FD_ISSET(sd, &readfds)) {
                std::string data = read_json_message(sd);
                if (!data.empty()) {
                    if (reader.parse(data, command)) {
                        std::cout << "Received JSON command: " << command << std::endl;
                        pthread_mutex_lock(&simulation_lock);
                        inputs = command;
                        pthread_mutex_unlock(&simulation_lock);
                    } else {
                        std::cerr << "Failed to parse JSON" << std::endl;
                    }
                }
            }
        }
    }
    return 0;
}
