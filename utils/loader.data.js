import fs from 'node:fs';
import * as XLSX from 'xlsx';

export default {
  watch: ['../data/副本嘉善管点管线字典.xlsx'],
  load(watchedFiles) {
    return watchedFiles.map((file) => {
        console.log('!读取文件')
      const workbook = XLSX.readFile(file);
      const sheetName = workbook.SheetNames[0]; // 获取第一个工作表
      const worksheet = workbook.Sheets[sheetName];
      const jsonData = XLSX.utils.sheet_to_json(worksheet); // 将工作表转换为 JSON
      console.log('!读取文件完成', jsonData)
      return jsonData;
    });
  }
};
