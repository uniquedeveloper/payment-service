import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {

  private apiUrl = 'http://127.0.0.1:8080/'; // Flask API endpoint

  constructor(private http: HttpClient) { }

  // get payments
  async getPayments(): Promise<any> {
    const response = await firstValueFrom(this.http.get(this.apiUrl + 'get_payments'));
    return response;
  }

  // delete payments
  async deletePaymentRecord(element_id: any): Promise<any> {
    console.log(element_id);
    const response = await firstValueFrom(this.http.delete(this.apiUrl + 'delete_payment/' + element_id));
    return response;
  }
}
