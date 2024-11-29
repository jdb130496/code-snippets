public class NextAfterTest {
    public static void main(String[] args) {
        if (args.length % 2 != 0) {
            System.err.println("Please provide pairs of arguments.");
            return;
        }

        for (int i = 0; i < args.length; i += 2) {
            // Determine if the input should be treated as float or double
            boolean isFloat = args[i].contains(".") && args[i + 1].contains(".");
            if (isFloat) {
                float start = Float.parseFloat(args[i]);
                float direction = Float.parseFloat(args[i + 1]);
                float result = Math.nextAfter(start, direction);
                System.out.println(result);
            } else {
                double start = Double.parseDouble(args[i]);
                double direction = Double.parseDouble(args[i + 1]);
                double result = Math.nextAfter(start, direction);
                System.out.println(result);
            }
        }
    }
}

