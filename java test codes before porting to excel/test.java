class test {
    public static void main(String[] args) {
        System.out.println(Math.nextAfter(-20, -21));
        System.out.println(Math.nextAfter(1, 0));
        System.out.println(Math.nextAfter(0.5f, 1.0f));
        System.out.println(Math.nextAfter(0.5f, 0.0f));
    }
}
