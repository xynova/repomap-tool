// JavaScript code for multi-language testing
class UserService {
    constructor() {
        this.users = [];
    }
    
    createUser(username, email) {
        const user = {
            id: this.users.length + 1,
            username,
            email,
            role: 'user'
        };
        this.users.push(user);
        return user;
    }
    
    findUser(id) {
        return this.users.find(user => user.id === id);
    }
    
    async processUser(user) {
        await new Promise(resolve => setTimeout(resolve, 100));
        return `Processed user: ${user.username}`;
    }
}

function calculateSum(numbers) {
    return numbers.reduce((sum, num) => sum + num, 0);
}

const userService = new UserService();
module.exports = { UserService, calculateSum };
