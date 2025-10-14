// TypeScript code for multi-language testing
interface User {
    id: number;
    username: string;
    email: string;
    role: 'admin' | 'user' | 'guest';
}

class UserService {
    private users: User[] = [];
    
    createUser(username: string, email: string): User {
        const user: User = {
            id: this.users.length + 1,
            username,
            email,
            role: 'user'
        };
        this.users.push(user);
        return user;
    }
    
    findUser(id: number): User | undefined {
        return this.users.find(user => user.id === id);
    }
    
    async processUser(user: User): Promise<string> {
        await new Promise(resolve => setTimeout(resolve, 100));
        return `Processed user: ${user.username}`;
    }
}

function calculateSum(numbers: number[]): number {
    return numbers.reduce((sum, num) => sum + num, 0);
}

const userService = new UserService();
export { User, UserService, calculateSum };
