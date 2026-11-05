import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** 无外部依赖的本地业务服务台；金额以最小单位整数记录。 */
public class Main {
    static final Path FILE = Path.of("records.tsv");
    static final List<Record> records = new ArrayList<>();
    static String[] states;
    static String[] categories;
    static class Record {
        long id, amount;
        String title, category, status, note;
        Record(long id, String title, String category, long amount, String status, String note) {
            this.id=id;this.title=title;this.category=category;this.amount=amount;this.status=status;this.note=note;
        }
        String serialize() {return id+"\t"+title+"\t"+category+"\t"+amount+"\t"+status+"\t"+note;}
    }
    static String clean(String value) {
        if(value.contains("\t") || value.contains("\n") || value.contains("\r")) throw new IllegalArgumentException("内容不能包含制表或换行");
        return value.trim();
    }
    static void add(String title, String category, long amount, String note) {
        title=clean(title);note=clean(note);
        if(title.isEmpty() || title.length()>80)throw new IllegalArgumentException("名称须为 1—80 字");
        if(!Arrays.asList(categories).contains(category))throw new IllegalArgumentException("分类不存在");
        if(amount<0 || amount>100000000)throw new IllegalArgumentException("数值超出范围");
        long id=records.stream().mapToLong(r->r.id).max().orElse(0)+1;
        records.add(new Record(id,title,category,amount,states[0],note));
    }
    static void advance(long id) {
        Record record=records.stream().filter(r->r.id==id).findFirst().orElseThrow(()->new IllegalArgumentException("记录不存在"));
        int index=Arrays.asList(states).indexOf(record.status);
        if(index<0 || index==states.length-1)throw new IllegalArgumentException("不能继续推进状态");
        record.status=states[index+1];
    }
    static void save() throws IOException {
        List<String> lines=new ArrayList<>();
        for(Record record:records)lines.add(record.serialize());
        Path temporary=Path.of("records.tmp");
        Files.write(temporary,lines,StandardCharsets.UTF_8);
        try {Files.move(temporary,FILE,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);}
        catch(AtomicMoveNotSupportedException ex){Files.move(temporary,FILE,StandardCopyOption.REPLACE_EXISTING);}
    }
    static void load() throws IOException {
        records.clear();
        if(!Files.exists(FILE))return;
        for(String line:Files.readAllLines(FILE,StandardCharsets.UTF_8)) {
            String[] parts=line.split("\t",-1);
            if(parts.length!=6)throw new IOException("记录格式错误，请检查备份");
            records.add(new Record(Long.parseLong(parts[0]),parts[1],parts[2],Long.parseLong(parts[3]),parts[4],parts[5]));
        }
    }
    static String cell(String value) {
        if(value.matches("^[=+@-].*"))value="'"+value;
        return "\""+value.replace("\"","\"\"")+"\"";
    }
    static void export() throws IOException {
        List<String> lines=new ArrayList<>();lines.add("\ufeff编号,名称,分类,数值,状态,说明");
        for(Record r:records)lines.add(r.id+","+cell(r.title)+","+cell(r.category)+","+r.amount+","+cell(r.status)+","+cell(r.note));
        Files.write(Path.of("export.csv"),lines,StandardCharsets.UTF_8);
    }
    static void test() throws Exception {
        records.clear();add("测试",categories[0],5,"模拟");
        if(records.size()!=1)throw new AssertionError("新增失败");
        boolean rejected=false;try{add("",categories[0],-1,"");}catch(IllegalArgumentException ex){rejected=true;}
        if(!rejected)throw new AssertionError("校验失败");
        for(int i=1;i<states.length;i++)advance(1);
        rejected=false;try{advance(1);}catch(IllegalArgumentException ex){rejected=true;}
        if(!rejected)throw new AssertionError("终态未拒绝");
        System.out.println("PASS: 新增、非法输入、状态推进、终态拒绝（测试不写业务文件）");
    }
    public static void main(String[] args) throws Exception {
        Properties config=new Properties();
        try(Reader reader=Files.newBufferedReader(Path.of("scenario.properties"),StandardCharsets.UTF_8)){config.load(reader);}
        states=config.getProperty("states").split(",");categories=config.getProperty("categories").split(",");
        if(args.length>0 && args[0].equals("--test")){test();return;}
        load();System.out.println(config.getProperty("title"));
        System.out.println("分类："+String.join(" / ",categories));
        System.out.println("命令：list [关键词] | add 名称|分类|整数数值|说明 | next 编号 | stats | export | quit");
        Scanner scanner=new Scanner(System.in,StandardCharsets.UTF_8);
        while(scanner.hasNextLine()) {
            String command=scanner.nextLine().trim();
            try {
                if(command.equals("quit"))break;
                if(command.startsWith("list")) {
                    String query=command.length()>4?command.substring(4).trim():"";
                    records.stream().filter(r->r.serialize().contains(query)).forEach(r->System.out.println(r.serialize()));
                } else if(command.startsWith("add ")) {
                    String[] parts=command.substring(4).split("\\|",-1);
                    if(parts.length!=4)throw new IllegalArgumentException("请填写四个字段，以 | 分隔");
                    add(parts[0],parts[1],Long.parseLong(parts[2]),parts[3]);save();System.out.println("已保存");
                } else if(command.startsWith("next ")) {advance(Long.parseLong(command.substring(5).trim()));save();System.out.println("已更新");}
                else if(command.equals("stats")) {System.out.println("共 "+records.size()+" 条，数值合计 "+records.stream().mapToLong(r->r.amount).sum());}
                else if(command.equals("export")) {export();System.out.println("已导出 export.csv");}
                else System.out.println("未知命令");
            } catch(IllegalArgumentException | IOException ex){System.out.println("操作失败："+ex.getMessage());}
        }
    }
}
