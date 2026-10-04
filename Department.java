class Department{
    int id;
    void display(){
        id=200;
        System.out.println("Id:"+id);
    }
}
class Departmentmain{
    public static void main(string args[])
    {
        Department d=new Department();
        d,display();
        d.display(202);
    }
}