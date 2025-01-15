import { Component, AfterViewInit, ViewChild, inject, ChangeDetectionStrategy } from '@angular/core';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { MatPaginator } from '@angular/material/paginator';
import { Route } from '@angular/router';
import { ApiService } from 'src/api.service';
import { MatDialog } from '@angular/material/dialog';
import { ItemDialogComponent } from 'src/item-dialog/item-dialog.component';
import { EditDialogComponent } from 'src/edit-dialog/edit-dialog.component';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-payment-list',
  templateUrl: './payment-list.component.html',
  styleUrls: ['./payment-list.component.css'],
})
export class PaymentListComponent {

  @ViewChild(MatPaginator) paginator: MatPaginator | null = null; // Reference to paginator
  @ViewChild(MatSort, {static: true}) sort: MatSort | undefined;
  isViewing = false;
  dialog = inject(MatDialog)
  title = 'payment-dashboard';
  displayedColumns: string[] = [
    "payee_first_name",
    "payee_last_name",
    "due_amount",
    "payee_payment_status",
    "total_due",
    "evidence",
    "action"
  ]; // columns to display
  dataSource= new MatTableDataSource<any>([]) ; // data source for the table

  constructor(
    private apiService: ApiService
  ) {}
  async ngOnInit() {
    try {
      // Fetch data asynchronously using await
      const response = await this.apiService.getPayments();
      this.dataSource = new MatTableDataSource(response);
      setTimeout(() => {
        if (this.paginator) {
          this.dataSource.paginator = this.paginator;
          this.dataSource.sort = this.sort as MatSort;
        }
      }, 1000);
      console.log(this.dataSource);
    // Initialize dataSource with the response data
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  }

  async ngAfterViewInit() {
    // Ensure paginator is initialized properly
    setTimeout(() => {
      if (this.paginator) {
        this.dataSource.paginator = this.paginator;
      }
    }, 1000);
  }

  applyFilter(event: KeyboardEvent): void {
    const input = event.target as HTMLInputElement; // Cast event.target to HTMLInputElement
    const filterValue = input.value.trim();  // Get property to filter
    this.dataSource.filter = filterValue.trim().toLocaleLowerCase();
  }

  toggleView(item:any) {
    const dialogRef = this.dialog.open(ItemDialogComponent, {data: item})
  }

  toggleEdit(item:any) {
    const dialogRef = this.dialog.open(EditDialogComponent, {data: item})
  }

  closeDisplayInfo() {
    this.isViewing = false;  // Set isViewing to false to hide the app-display-info component
  }

  async deletePaymentRecord(element: any) {
    try {
      const response = await this.apiService.deletePaymentRecord(element._id);
  
      if (response) {
        const index = this.dataSource.data.indexOf(element);
        if (index >= 0) {
          this.dataSource.data.splice(index, 1);
          alert("Record deleted Sucessfully!!");
          this.dataSource._updateChangeSubscription();  // Manually trigger change detection
        }
      }
    } catch (error) {
      // Handle any error that occurs during the API call
      alert('There was an error deleting the item. Please try again.');
      console.error('Error deleting item:', error);
    }
  }  

}
